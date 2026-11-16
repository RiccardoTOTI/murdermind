"""AGENT 8 — Narrative Writer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import NARRATIVE_WRITER_PROMPT
from murdermind.schemas.mystery import AgentCritique, MysteryProject, NarrativeMaterials


class NarrativeWriterAgent(BaseNarrativeAgent):
    """Writes atmospheric introductions, prologue speech, suggested character dialogues, and printable documents."""

    name = "NarrativeWriter"
    role_title = "AGENT 8 – Narrative Writer"
    phase_name = "Fase 8 – Narrative Production"
    system_prompt = NARRATIVE_WRITER_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        concept = project.concept
        world = project.world
        sol = project.plot.secret_solution
        revision_note = self.format_critique_feedback(critiques)

        char_list_str = ", ".join(f"{c.character_id} ({c.name} - {c.role})" for c in project.characters)
        clue_list_str = ", ".join(f"{c.clue_id} ({c.title})" for c in project.clues[:4])

        user_prompt = (
            f"Lingua: {cfg.language} | Tono: {cfg.effective_tone}\n"
            f"Mistero: {concept.title} — {concept.tagline}\n"
            f"Ambientazione: {world.era_and_place or cfg.effective_setting}\n"
            f"Vittima: {concept.victim_name} ({concept.victim_role})\n"
            f"Personaggi: {char_list_str}\n"
            f"Indizi principali: {clue_list_str}\n"
            "Scrivi l'introduzione narrativa, il discorso di apertura, battute suggerite per i personaggi e 3 documenti in-game (letter, message, evidence) in JSON.\n"
            "NON svelare il nome del colpevole nell'introduzione pubblica.\n"
            f"{revision_note}"
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            intro = str(
                raw.get("introduction_md")
                or (
                    f"# {concept.title}\n\n"
                    f"*{concept.tagline}*\n\n"
                    f"{world.backstory or concept.hook}\n\n"
                    f"La serata in **{world.era_and_place or cfg.effective_setting}** prometteva di essere indimenticabile, "
                    f"ma l'improvvisa morte di **{concept.victim_name}** ({concept.victim_role}) ha trasformato il banchetto "
                    "in una serrata caccia alla verità. Nessuno può lasciare la sala finché il colpevole non sarà smascherato."
                )
            )
            prologue = str(
                raw.get("prologue_speech_md")
                or (
                    f"«Signore e signori, chiudete le porte. **{concept.victim_name}** è stato trovato senza vita in **{sol.murder_location}**. "
                    "Tra di voi siede chi ha colpito nell'ombra, ma ciascuno di voi custodisce segreti che preferirebbe seppellire. "
                    "Osservate gli indizi, interrogate i presenti e ricordate: un dettaglio fuori posto nell'orario o nell'alibi tradirà l'assassino.»"
                )
            )

            raw_dialogues = raw.get("character_dialogues")
            dialogues: Dict[str, List[str]] = {}
            if isinstance(raw_dialogues, dict):
                for k, v in raw_dialogues.items():
                    dialogues[str(k)] = ensure_str_list(v)
            for c in project.characters:
                if c.character_id not in dialogues or not dialogues[c.character_id]:
                    dialogues[c.character_id] = [
                        f"«Tutti sapevano che {concept.victim_name} si era fatto molti nemici, ma il mio alibi è solido: {c.alibi}»",
                        f"«Prima di puntare il dito contro di me, chiedete piuttosto cosa stava nascondendo {c.relationships[0].target_name if c.relationships else 'il nostro ospite'}!»",
                    ]

            raw_conf = raw.get("confidential_communications")
            confidential: Dict[str, str] = {}
            if isinstance(raw_conf, dict):
                for k, v in raw_conf.items():
                    confidential[str(k)] = str(v)
            for c in project.characters:
                if c.character_id not in confidential or not confidential[c.character_id]:
                    confidential[c.character_id] = (
                        f"[COMUNICAZIONE RISERVATA PER {c.name.upper()}]: "
                        f"Qualcuno ha notato i tuoi movimenti intorno alle {sol.time_of_death}. "
                        f"Proteggi il tuo segreto ({c.secret}) e usa ciò che sai ({c.known_facts[0] if c.known_facts else 'i tuoi sospetti'}) per guidare gli interrogatori."
                    )

            raw_docs = raw.get("documents")
            docs: List[Dict[str, Any]] = []
            if isinstance(raw_docs, list):
                for idx, d in enumerate(raw_docs, start=1):
                    if isinstance(d, dict):
                        dtype = str(d.get("doc_type") or "letter").lower()
                        if dtype not in ("letter", "message", "evidence"):
                            dtype = ("letter", "message", "evidence")[(idx - 1) % 3]
                        docs.append(
                            {
                                "doc_id": f"doc_{idx:02d}",
                                "doc_type": dtype,
                                "title": str(d.get("title") or f"Documento #{idx}"),
                                "sender": str(d.get("sender") or concept.victim_name),
                                "recipient": str(d.get("recipient") or "Riservato"),
                                "content": str(
                                    d.get("content")
                                    or "Testo probatorio rinvenuto durante la perquisizione."
                                ),
                                "related_clue_id": str(
                                    d.get("related_clue_id")
                                    or (project.clues[idx - 1].clue_id if idx <= len(project.clues) else "clue_01")
                                ),
                            }
                        )

            if len(docs) < 3:
                c0 = project.characters[0].name if project.characters else "Un Ospite"
                c1 = project.characters[1].name if len(project.characters) > 1 else "Il Destinatario"
                docs = [
                    {
                        "doc_id": "doc_01",
                        "doc_type": "letter",
                        "title": f"Lettera incompiuta di {concept.victim_name}",
                        "sender": concept.victim_name,
                        "recipient": "Notaio / Archivio Riservato",
                        "content": (
                            f"Stasera metterò fine a questo ricatto. So perfettamente chi ha interesse a "
                            f"farmi tacere riguardo a: {sol.motive}. Se dovesse accadermi qualcosa tra le {sol.time_of_death}, "
                            f"cercate le prove in {sol.murder_location}."
                        ),
                        "related_clue_id": project.clues[0].clue_id if project.clues else "clue_01",
                    },
                    {
                        "doc_id": "doc_02",
                        "doc_type": "message",
                        "title": "Biglietto urgente piegato in quattro",
                        "sender": c0,
                        "recipient": c1,
                        "content": (
                            "Non fare parola con nessuno del nostro incontro delle 20:45. "
                            "Se scoprono cosa stavamo trattando, penseranno che siamo coinvolti nell'omicidio!"
                        ),
                        "related_clue_id": project.clues[1].clue_id if len(project.clues) > 1 else "clue_02",
                    },
                    {
                        "doc_id": "doc_03",
                        "doc_type": "evidence",
                        "title": f"Verbale di Sopralluogo — {sol.murder_location}",
                        "sender": "Ispezione Scena del Crimine",
                        "recipient": "Tutti gli Investigatori",
                        "content": (
                            f"Luogo del ritrovamento: {sol.murder_location}.\n"
                            f"Ora stimata del decesso: {sol.time_of_death}.\n"
                            f"Causa / Arma rilevata: {sol.murder_weapon}.\n"
                            f"Nota investigativa: {sol.alibi_flaw}"
                        ),
                        "related_clue_id": project.clues[2].clue_id if len(project.clues) > 2 else "clue_03",
                    },
                ]

            return {
                "introduction_md": intro,
                "prologue_speech_md": prologue,
                "character_dialogues": dialogues,
                "confidential_communications": confidential,
                "documents": docs,
            }

        narrative = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=NarrativeMaterials,
            temperature=0.65,
            max_tokens=1200,
            normalizer=normalize,
        )
        project.narrative = narrative
        action = "revision" if critiques else "generate_narrative"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=(
                f"Materiali narrativi scritti: introduzione, prologo, battute per "
                f"{len(narrative.character_dialogues)} personaggi e {len(narrative.documents)} documenti stampabili."
            ),
            status="revised" if critiques else "completed",
            details={"document_ids": [d.doc_id for d in narrative.documents]},
        )
        return project
