"""AGENT 3 — Plot Architect."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from murdermind.agents.base import BaseNarrativeAgent, ensure_str_list
from murdermind.prompts.system_prompts import PLOT_ARCHITECT_PROMPT
from murdermind.schemas.mystery import AgentCritique, MainPlot, MysteryProject


class PlotArchitectAgent(BaseNarrativeAgent):
    """Designs the central murder, secret canonical solution, timeline, and red herrings."""

    name = "PlotArchitect"
    role_title = "AGENT 3 – Plot Architect"
    phase_name = "Fase 3 – Plot Design"
    system_prompt = PLOT_ARCHITECT_PROMPT

    def run(
        self,
        project: MysteryProject,
        critiques: Optional[List[AgentCritique]] = None,
    ) -> MysteryProject:
        cfg = project.config
        concept = project.concept
        world = project.world
        total_chars = max(3, cfg.total_characters)
        char_ids = [f"char_{i:02d}" for i in range(1, total_chars + 1)]
        revision_note = self.format_critique_feedback(critiques)

        locations_hint = (
            ", ".join(loc.name for loc in world.locations)
            if world.locations
            else cfg.effective_setting
        )

        user_prompt = (
            f"Lingua: {cfg.language}\n"
            f"Titolo: {concept.title}\n"
            f"Vittima: {concept.victim_name} ({concept.victim_role})\n"
            f"Sintesi delitto: {concept.crime_summary}\n"
            f"Ambientazione e luoghi: {world.era_and_place or cfg.effective_setting} | Luoghi: {locations_hint}\n"
            f"ID personaggi disponibili per il colpevole e la timeline: {', '.join(char_ids)}\n"
            f"Scegli UNO di questi ID come colpevole (es. char_02) e definisci soluzione segreta + almeno 4 eventi in timeline.\n"
            f"{revision_note}\n"
            "Genera la trama principale e la soluzione segreta in JSON."
        )

        def normalize(raw: Dict[str, Any]) -> Dict[str, Any]:
            sol_raw = raw.get("secret_solution")
            if not isinstance(sol_raw, dict):
                sol_raw = {}

            culprit_id = str(sol_raw.get("culprit_id") or raw.get("culprit_id") or "char_01").strip()
            if culprit_id not in char_ids:
                culprit_id = char_ids[0]

            secret_solution = {
                "victim_name": str(sol_raw.get("victim_name") or concept.victim_name or "Lorenzo Valenti"),
                "culprit_id": culprit_id,
                "culprit_name": str(sol_raw.get("culprit_name") or raw.get("culprit_name") or "Il Colpevole"),
                "motive": str(
                    sol_raw.get("motive")
                    or raw.get("motive")
                    or "Impedire alla vittima di rendere pubblico un ricatto finanziario e familiare."
                ),
                "murder_weapon": str(
                    sol_raw.get("murder_weapon")
                    or raw.get("murder_weapon")
                    or "Veleno ad azione rapida versato nel calice riservato"
                ),
                "murder_location": str(
                    sol_raw.get("murder_location")
                    or raw.get("murder_location")
                    or (world.locations[0].name if world.locations else "Studio privato")
                ),
                "time_of_death": str(
                    sol_raw.get("time_of_death") or raw.get("time_of_death") or "21:15 - 21:30"
                ),
                "opportunity_and_dynamics": str(
                    sol_raw.get("opportunity_and_dynamics")
                    or raw.get("opportunity_and_dynamics")
                    or "Il colpevole ha sfruttato un breve momento di isolamento prima del brindisi principale."
                ),
                "alibi_flaw": str(
                    sol_raw.get("alibi_flaw")
                    or raw.get("alibi_flaw")
                    or "Dichiara di essere rimasto nel salone, ma un oggetto personale e un testimone lo collocano vicino allo studio alle 21:20."
                ),
                "deduction_chain": ensure_str_list(
                    sol_raw.get("deduction_chain") or raw.get("deduction_chain"),
                    [
                        "Ricostruire l'orario esatto della morte (21:15 - 21:30)",
                        f"Verificare la contraddizione nell'alibi di {culprit_id}",
                        f"Collegare l'arma del delitto e il movente segreto a {culprit_id}",
                    ],
                ),
            }

            raw_timeline = raw.get("timeline")
            timeline: List[Dict[str, Any]] = []
            if isinstance(raw_timeline, list):
                for idx, item in enumerate(raw_timeline, start=1):
                    if isinstance(item, dict):
                        involved = ensure_str_list(item.get("involved_character_ids"))
                        valid_involved = [cid for cid in involved if cid in char_ids]
                        if not valid_involved:
                            valid_involved = [char_ids[(idx - 1) % len(char_ids)]]
                        timeline.append(
                            {
                                "event_id": f"evt_{idx:02d}",
                                "timestamp": str(item.get("timestamp") or f"{19 + idx}:00"),
                                "title": str(item.get("title") or f"Evento {idx}"),
                                "description": str(
                                    item.get("description") or f"Sviluppo chiave della serata ({idx})."
                                ),
                                "involved_character_ids": valid_involved,
                                "location": str(
                                    item.get("location") or secret_solution["murder_location"]
                                ),
                                "is_public": bool(item.get("is_public", idx == 1)),
                                "is_crime_event": bool(
                                    item.get("is_crime_event", idx == len(raw_timeline) - 1)
                                ),
                            }
                        )

            if len(timeline) < 4:
                second_id = char_ids[1] if len(char_ids) > 1 else char_ids[0]
                third_id = char_ids[2] if len(char_ids) > 2 else char_ids[0]
                timeline = [
                    {
                        "event_id": "evt_01",
                        "timestamp": "20:00",
                        "title": "Arrivo degli ospiti e tensione iniziale",
                        "description": f"{concept.victim_name} accoglie i presenti e annuncia una rivelazione imminente.",
                        "involved_character_ids": char_ids[:3],
                        "location": "Salone principale",
                        "is_public": True,
                        "is_crime_event": False,
                    },
                    {
                        "event_id": "evt_02",
                        "timestamp": "20:45",
                        "title": "Discussione accesa in privato",
                        "description": f"Viene udito un alterco riservato tra la vittima e {second_id}.",
                        "involved_character_ids": [second_id],
                        "location": "Corridoio orientale",
                        "is_public": False,
                        "is_crime_event": False,
                    },
                    {
                        "event_id": "evt_03",
                        "timestamp": secret_solution["time_of_death"],
                        "title": "L'omicidio",
                        "description": (
                            f"{culprit_id} colpisce {concept.victim_name} in {secret_solution['murder_location']} "
                            f"usando {secret_solution['murder_weapon']}."
                        ),
                        "involved_character_ids": [culprit_id],
                        "location": secret_solution["murder_location"],
                        "is_public": False,
                        "is_crime_event": True,
                    },
                    {
                        "event_id": "evt_04",
                        "timestamp": "21:45",
                        "title": "Scoperta del corpo",
                        "description": f"Il corpo di {concept.victim_name} viene scoperto e nessuno può lasciare l'edificio.",
                        "involved_character_ids": [third_id, culprit_id],
                        "location": secret_solution["murder_location"],
                        "is_public": True,
                        "is_crime_event": False,
                    },
                ]
            else:
                if not any(e.get("is_crime_event") for e in timeline):
                    timeline[-2]["is_crime_event"] = True
                    if culprit_id not in timeline[-2]["involved_character_ids"]:
                        timeline[-2]["involved_character_ids"].append(culprit_id)

            return {
                "crime_overview": str(
                    raw.get("crime_overview")
                    or f"{concept.victim_name} viene assassinato in {secret_solution['murder_location']}; la chiave risiede nella falla dell'alibi di {culprit_id}."
                ),
                "secret_solution": secret_solution,
                "timeline": timeline,
                "red_herrings": ensure_str_list(
                    raw.get("red_herrings"),
                    [
                        "Un litigio pubblico avvenuto poco prima del delitto attira i sospetti su un innocente",
                        "Un documento strappato sembra accusare un altro ospite ma riguarda un segreto secondario",
                    ],
                ),
                "alternative_developments": ensure_str_list(
                    raw.get("alternative_developments"),
                    [
                        "Se il colpevole viene smascherato presto, tenta di scaricare la colpa sul complice inconsapevole."
                    ],
                ),
            }

        plot = self.llm.generate_structured(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            schema_cls=MainPlot,
            temperature=0.5,
            max_tokens=1100,
            normalizer=normalize,
        )
        project.plot = plot
        action = "revision" if critiques else "generate_plot"
        project.log_activity(
            phase=self.phase_name,
            agent_name=self.name,
            action=action,
            summary=(
                f"Trama definita — Colpevole: {plot.secret_solution.culprit_id} | "
                f"Arma: {plot.secret_solution.murder_weapon} | Eventi timeline: {len(plot.timeline)}"
            ),
            status="revised" if critiques else "completed",
            details=plot.model_dump(),
        )
        return project
