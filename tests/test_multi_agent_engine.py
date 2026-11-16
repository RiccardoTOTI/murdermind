"""Tests for M2 (3-agent MVP + review cycle) and M3 (Full 10-agent engine + Information Graph Validator)."""

from __future__ import annotations

import json
import httpx
import pytest

from murdermind.config import LLMConfig, ProviderMode
from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.core.llm_client import OpenAICompatibleClient
from murdermind.core.orchestrator import MurderMysteryOrchestrator
from murdermind.schemas.mystery import AgentCritique, StoryConfig


def make_mock_client(trigger_first_review_fail: bool = False) -> OpenAICompatibleClient:
    """Create a deterministic mock OpenAI-compatible client for fast multi-agent tests."""
    review_calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        sys_prompt = body["messages"][0]["content"]

        if "AGENT 1" in sys_prompt:
            payload = {
                "title": "L'Ultimo Calice a Villa Morosini",
                "tagline": "Nessun brindisi resta impunito",
                "hook": "Durante una cena di gala nella storica Villa Morosini, il collezionista Lorenzo Valenti crolla avvelenato.",
                "victim_name": "Lorenzo Valenti",
                "victim_role": "Collezionista d'arte e banchiere",
                "crime_summary": "Avvelenato nel suo studio privato tra le 21:15 e le 21:30.",
                "atmosphere_directive": "Thriller elegante con tensione psicologica",
                "design_pillars": ["Alibi incrociati", "Ricatti d'arte", "Soluzione deducibile"],
            }
        elif "AGENT 2" in sys_prompt:
            payload = {
                "era_and_place": "Villa Morosini, Lago di Como, epoca contemporanea",
                "social_cultural_context": "Alta finanza e collezionismo d'arte internazionale.",
                "atmosphere": "Tempesta sul lago, luci calde nei saloni e ombre nei corridoi.",
                "backstory": "Lorenzo Valenti ha convocato debitori e soci per un annuncio sul suo testamento.",
                "characteristic_elements": ["Passaggio segreto dietro la libreria", "Cantina storica"],
                "locations": [
                    {
                        "location_id": "loc_01",
                        "name": "Studio Privato",
                        "description": "Stanza blindata con opere d'arte e cassaforte.",
                        "hidden_detail": "Accesso segreto dalla Galleria Orientale.",
                    }
                ],
                "world_secrets": ["Il passaggio segreto permette di entrare nello studio senza essere visti dal salone."],
                "public_facts": ["Il temporale ha isolato la villa dalle 20:00."],
            }
        elif "AGENT 3" in sys_prompt:
            payload = {
                "crime_overview": "char_02 ha versato digitale purpurea nel calice privato di Lorenzo Valenti.",
                "secret_solution": {
                    "victim_name": "Lorenzo Valenti",
                    "culprit_id": "char_02",
                    "culprit_name": "Dott. Valerio Santi",
                    "motive": "Valenti aveva scoperto che Santi falsificava perizie mediche e ricettazioni.",
                    "murder_weapon": "Estratto di digitale purpurea nel decanter riservato",
                    "murder_location": "Studio Privato",
                    "time_of_death": "21:15 - 21:30",
                    "opportunity_and_dynamics": "È passato dalla Galleria Orientale alle 21:20.",
                    "alibi_flaw": "Sostiene di aver telefonato in veranda alle 21:20, ma la linea era interrotta dal temporale e il suo gemello da polso è rimasto nello Studio.",
                    "deduction_chain": [
                        "L'arma richiede competenze chimiche/mediche (char_02)",
                        "La linea telefonica era fuori uso alle 21:20, smentendo l'alibi di char_02",
                        "Il gemello con iniziali V.S. è stato trovato vicino al decanter nello Studio Privato",
                    ],
                },
            }
        elif "AGENT 4" in sys_prompt:
            user_prompt = body["messages"][1]["content"]
            is_culprit = "È IL COLPEVOLE" in user_prompt
            payload = {
                "name": "Dott. Valerio Santi" if is_culprit else "Contessa Elena Morosini",
                "role": "Medico personale" if is_culprit else "Socia della galleria",
                "background": "Legato da anni alla vittima.",
                "personality": "Freddo e calcolatore" if is_culprit else "Orgogliosa e magnetica",
                "goals": ["Sviare i sospetti", "Recuperare i documenti"],
                "secret": (
                    "Ha avvelenato il decanter nello Studio alle 21:20"
                    if is_culprit
                    else "Aveva sottratto un quadro per coprire un debito"
                ),
                "alibi": (
                    "Dichiara di essere stato in veranda al telefono alle 21:20"
                    if is_culprit
                    else "Era nel Salone delle Feste con il maggiordomo"
                ),
                "motive": "Evitare la denuncia per frode" if is_culprit else "Conflitto societario",
                "known_facts": ["Alle 21:10 la linea telefonica fissa era muta a causa del temporale"],
                "hidden_facts": ["Ha perso un gemello da polso vicino alla libreria"],
                "what_can_reveal": "Rivela ciò che sa sulla linea telefonica se interrogato.",
                "reaction_to_accusation": "Minimizza e chiede prove materiali.",
            }
        elif "AGENT 9" in sys_prompt:
            review_calls["count"] += 1
            if trigger_first_review_fail and review_calls["count"] == 1:
                payload = {
                    "passed": False,
                    "coherence_score": 65,
                    "summary": "Richiesto approfondimento sulla timeline in PlotArchitect.",
                    "critiques": [
                        {
                            "target_agent": "PlotArchitect",
                            "issue_type": "timeline_detail",
                            "severity": "major",
                            "description": "Rendere più esplicito l'orario del ritrovamento.",
                            "suggested_fix": "Confermare l'evento delle 21:45 nella timeline.",
                            "affected_ids": ["evt_04"],
                        }
                    ],
                }
            else:
                payload = {
                    "passed": True,
                    "coherence_score": 92,
                    "summary": "Grafo narrativo coerente e soluzione deducibile.",
                    "critiques": [],
                }
        else:
            payload = {}

        return httpx.Response(
            200,
            json={
                "model": "unsloth/Qwen3.5-2B",
                "choices": [{"message": {"role": "assistant", "content": json.dumps(payload)}}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 80},
            },
        )

    cfg = LLMConfig(provider=ProviderMode.LOCAL, api_key="mock")
    return OpenAICompatibleClient(config=cfg, transport=httpx.MockTransport(handler))


def test_m2_mvp_three_agents_and_revision_cycle() -> None:
    client = make_mock_client(trigger_first_review_fail=True)
    orchestrator = MurderMysteryOrchestrator(llm_client=client)
    config = StoryConfig(
        setting_preset="Villa nobiliare",
        num_playable_characters=3,
        num_npcs=1,
        max_review_iterations=2,
    )
    project = orchestrator.create_project(config)
    project = orchestrator.run_mvp_pipeline(project)

    assert project.status == "completed"
    assert project.concept.title == "L'Ultimo Calice a Villa Morosini"
    assert project.plot.secret_solution.culprit_id == "char_02"
    assert len(project.characters) == 4
    culprit = project.get_culprit()
    assert culprit is not None
    assert culprit.character_id == "char_02"
    assert culprit.is_culprit is True
    # Verify that the review cycle ran twice (first triggered revision on PlotArchitect, second passed)
    assert len(project.reviews) == 2
    assert project.reviews[0].passed is True or any(c.resolved for c in project.reviews[0].critiques)
    assert project.reviews[-1].passed is True


def test_m3_full_ten_agent_pipeline_and_graph_consistency() -> None:
    client = make_mock_client(trigger_first_review_fail=False)
    orchestrator = MurderMysteryOrchestrator(llm_client=client)
    config = StoryConfig(
        setting_preset="Villa nobiliare",
        num_playable_characters=3,
        num_npcs=1,
        subplots_amount="Poche",
        max_review_iterations=2,
    )
    project = orchestrator.create_project(config)
    project = orchestrator.run_full_pipeline(project)

    assert project.status == "completed"
    assert len(project.world.locations) >= 3
    assert len(project.characters) == 4
    assert len(project.subplots) >= 2
    assert len(project.clues) >= 4
    assert len(project.gameplay.phases) == 3
    assert len(project.narrative.documents) >= 3
    assert "Manuale del Master" in project.final_production.master_manual_md
    assert "SOLUZIONE SEGRETA DEL MASTER" in project.final_production.secret_resolution_md

    # Verify full graph validator reports zero structural errors
    critiques = InformationGraphValidator.validate_full_graph(project)
    assert critiques == []


def test_live_qwen_mvp_three_agents_generation() -> None:
    client = OpenAICompatibleClient()
    if not client.ping_local():
        pytest.skip("Local LLM endpoint at 127.0.0.1:8888 is not reachable")

    orchestrator = MurderMysteryOrchestrator(llm_client=client)
    config = StoryConfig(
        title_hint="Ombre sul Treno di Mezzanotte",
        setting_preset="Treno",
        num_playable_characters=3,
        num_npcs=0,
        complexity="Semplice",
        duration_minutes=60,
        narrative_tone="Noir",
        max_review_iterations=1,
    )
    project = orchestrator.create_project(config)
    project = orchestrator.run_mvp_pipeline(project)

    assert project.status == "completed"
    assert len(project.concept.title) > 0
    assert len(project.characters) == 3
    assert project.get_culprit() is not None
    assert len(project.plot.timeline) >= 3
    assert len(project.reviews) >= 1
