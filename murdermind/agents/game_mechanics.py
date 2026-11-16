"""AGENT 7 — Game Mechanics Designer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import GAME_MECHANICS_PROMPT
from murdermind.schemas.mystery import AgentCritique, GameplayStructure, MysteryProject


class GameMechanicsAgent(BaseNarrativeAgent):
    """Transforms the mystery into structured playable phases, interrogation rules, and victory conditions."""

    name = "GameMechanicsDesigner"
    role_title = "AGENT 7 – Game Mechanics Designer"
    phase_name = "Fase 7 – Game Design"
    system_prompt = GAME_MECHANICS_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        clue_ids = [c.clue_id for c in project.clues] or ["clue_01", "clue_02", "clue_03", "clue_04"]
        revision_note = self.format_critique_feedback(critiques)

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Mistero: {project.concept.title} | Durata totale: {cfg.duration_minutes} minuti\n"
            f"Modalità di gioco: {cfg.gameplay_mode} | Presenza Master: {cfg.master_mode}\n"
            f"Complessità: {cfg.complexity}\n"
            f"Indizi disponibili da distribuire nelle 3 fasi: {', '.join(clue_ids)}\n"
            f"{revision_note}\n"
            "Progetta la struttura giocabile in 3 fasi, meccaniche di interrogatorio, accuse e vittoria in JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            phase_dur = max(15, cfg.duration_minutes // 3)
            raw_phases = raw.get("phases")
            phases: List[Dict[str, Any]] = []
            if isinstance(raw_phases, list):
                for idx, p in enumerate(raw_phases, start=1):
                    if isinstance(p, dict):
                        p_clues = [
                            c.clue_id for c in project.clues if c.discovery_phase == idx
                        ] or [clue_ids[(idx - 1) % len(clue_ids)]]
                        phases.append(
                            {
                                "phase_number": idx,
                                "title": str(p.get("title") or f"Fase {idx}"),
                                "duration_minutes": int(p.get("duration_minutes") or phase_dur),
                                "objectives": ensure_str_list(
                                    p.get("objectives"),
                                    [f"Raccogliere informazioni della Fase {idx} e confrontare gli alibi"],
                                ),
                                "revealed_clue_ids": ensure_str_list(
                                    p.get("revealed_clue_ids"), p_clues
                                ),
                                "scheduled_events": ensure_str_list(
                                    p.get("scheduled_events"),
                                    [f"Rivelazione degli indizi di Fase {idx}"],
                                ),
                                "interrogation_mechanics": str(
                                    p.get("interrogation_mechanics")
                                    or "Dialoghi incrociati tra i sospettati e domande dirette sugli alibi."
                                ),
                            }
                        )

            if len(phases) < 3:
                p1_clues = [c.clue_id for c in project.clues if c.discovery_phase == 1] or clue_ids[:2]
                p2_clues = [c.clue_id for c in project.clues if c.discovery_phase == 2] or clue_ids[1:3]
                p3_clues = [c.clue_id for c in project.clues if c.discovery_phase >= 3] or clue_ids[2:]
                phases = [
                    {
                        "phase_number": 1,
                        "title": "Fase 1: Presentazioni, Alibi e Primi Sospetti",
                        "duration_minutes": phase_dur,
                        "objectives": [
                            "Ogni giocatore si presenta secondo la propria scheda pubblica",
                            "Condivisione degli alibi iniziali ed esame dei primi indizi",
                        ],
                        "revealed_clue_ids": p1_clues,
                        "scheduled_events": [
                            "Lettura dell'introduzione e scoperta del delitto",
                            "Apertura della Busta Indizi Fase 1",
                        ],
                        "interrogation_mechanics": "Conversazioni libere in piccoli gruppi per verificare chi era con chi.",
                    },
                    {
                        "phase_number": 2,
                        "title": "Fase 2: Contraddizioni, Sottotrame e Colpi di Scena",
                        "duration_minutes": phase_dur,
                        "objectives": [
                            "Incrociare gli indizi di Fase 2 con gli alibi dichiarati",
                            "Risolvere o sfruttare le sottotrame personali e i ricatti",
                        ],
                        "revealed_clue_ids": p2_clues,
                        "scheduled_events": [
                            "Consegna delle comunicazioni riservate di metà serata",
                            "Apertura della Busta Indizi Fase 2",
                        ],
                        "interrogation_mechanics": "Ogni personaggio può porre una domanda pubblica vincolante a un altro sospettato.",
                    },
                    {
                        "phase_number": 3,
                        "title": "Fase 3: La Prova Decisiva e le Accuse Finali",
                        "duration_minutes": max(15, cfg.duration_minutes - 2 * phase_dur),
                        "objectives": [
                            "Analizzare gli ultimi documenti probatori",
                            "Compilare la scheda di accusa finale (Colpevole, Arma, Movente, Falla nell'alibi)",
                        ],
                        "revealed_clue_ids": p3_clues,
                        "scheduled_events": [
                            "Rivelazione degli indizi di Fase 3",
                            "Dichiarazione delle accuse e lettura della Soluzione Finale",
                        ],
                        "interrogation_mechanics": "Confronto finale in plenaria: 2 minuti per ciascun sospettato per difendersi.",
                    },
                ]

            return {
                "phases": phases,
                "information_distribution_rules": str(
                    raw.get("information_distribution_rules")
                    or (
                        f"Modalità '{cfg.master_mode}': le schede personaggio sono rigorosamente individuali; "
                        "gli indizi vengono sbloccati progressivamente all'inizio di ciascuna fase."
                    )
                ),
                "accusation_mechanics": str(
                    raw.get("accusation_mechanics")
                    or (
                        "Al termine della Fase 3 ogni giocatore compila in segreto il modulo d'accusa indicando: "
                        "1) Chi è l'assassino, 2) Con quale arma/metodo ha agito, 3) Qual è il movente, "
                        "4) Quale indizio smentisce il suo alibi."
                    )
                ),
                "victory_conditions": str(
                    raw.get("victory_conditions")
                    or (
                        "+3 punti per l'identificazione del colpevole, +2 punti per il movente corretto, "
                        "+2 punti per la falla nell'alibi, +2 punti se hai raggiunto l'obiettivo della tua sottotrama; "
                        "il colpevole vince se meno della metà dei giocatori lo accusa correttamente."
                    )
                ),
                "master_notes": str(
                    raw.get("master_notes")
                    or (
                        "Mantieni il ritmo scandendo i passaggi di fase durante le portate della cena. "
                        "Se i giocatori si bloccano su un depistaggio, ricorda loro di confrontare gli orari della timeline."
                    )
                ),
            }

        gameplay = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=GameplayStructure,
            temperature=0.55,
            max_tokens=1000,
            normalizer=normalize,
        )
        project.gameplay = gameplay
        action = "revision" if critiques else "generate_gameplay"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=f"Meccaniche di gioco definite in {len(gameplay.phases)} fasi ({cfg.duration_minutes} min totali).",
            status="revised" if critiques else "completed",
            details=gameplay.model_dump(),
        )
        return project
