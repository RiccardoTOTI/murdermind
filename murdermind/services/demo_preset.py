"""Complete playable Demo Murder Mystery case for instant inspection and Hugging Face Space showcase."""

from __future__ import annotations

from murdermind.agents.final_producer import FinalGameProducerAgent
from murdermind.core.graph_validator import InformationGraphValidator
from murdermind.schemas.mystery import (
    CharacterProfile,
    CharacterRelationship,
    ClueItem,
    FinalProductionSuite,
    GamePhase,
    GameplayStructure,
    InGameDocument,
    LocationItem,
    MainPlot,
    MysteryProject,
    NarrativeMaterials,
    ReviewReport,
    SecretSolution,
    StoryConcept,
    StoryConfig,
    SubplotItem,
    TimelineEvent,
    WorldState,
)


def build_demo_mystery_project() -> MysteryProject:
    """Return a rich, complete, playable Italian Murder Mystery case ('L'Ultimo Brindisi a Villa Morosini')."""
    config = StoryConfig(
        title_hint="L'Ultimo Brindisi a Villa Morosini",
        setting_preset="Villa nobiliare",
        custom_setting="Villa storica sul Lago di Como durante un nubifragio autunnale",
        num_playable_characters=4,
        num_npcs=1,
        complexity="Intermedia",
        duration_minutes=90,
        master_mode="Con master",
        subplots_amount="Medie",
        narrative_tone="Thriller",
        gameplay_mode="A fasi",
        custom_constraints="Il delitto avviene con un veleno raro versato nel decanter dello studio privato.",
        language="Italiano",
        max_review_iterations=2,
    )

    concept = StoryConcept(
        title="L'Ultimo Brindisi a Villa Morosini",
        tagline="Quattro invitati, un testamento segreto e un calice fatale sul Lago di Como",
        hook=(
            "Il celebre collezionista d'arte e finanziere Lorenzo Valenti ha convocato nella sua isolata "
            "villa sul Lago di Como quattro persone a lui legate da affari, debiti e segreti. Poco prima "
            "dell'annuncio di mezzanotte, Valenti viene trovato senza vita nel suo studio chiuso dall'interno."
        ),
        victim_name="Lorenzo Valenti",
        victim_role="Collezionista d'arte e patriarca finanziario",
        crime_summary=(
            "Lorenzo Valenti è stato avvelenato tra le 21:15 e le 21:30 nel suo Studio Privato con "
            "digitale concentrata versata nel decanter di brandy riservato."
        ),
        atmosphere_directive="Thriller psicologico elegante: pioggia battente, segreti d'alta società e tensione claustrofobica.",
        design_pillars=[
            "Ogni sospettato ha un movente reale e un segreto da proteggere",
            "Catena deduttiva basata su orari, competenze mediche e accesso al passaggio segreto",
            "Separazione netta tra informazioni pubbliche, segreti personali e soluzione del Master",
        ],
    )

    world = WorldState(
        era_and_place="Villa Morosini, sponda occidentale del Lago di Como — Giorni nostri",
        social_cultural_context=(
            "Un'élite di collezionisti, professionisti affermati ed eredi sull'orlo del tracollo "
            "finanziario, disposti a tutto pur di salvare la propria reputazione."
        ),
        atmosphere=(
            "Un violento nubifragio ha interrotto la linea telefonica fissa e bloccato il cancello "
            "principale. I lampadari di cristallo tremano ad ogni tuono."
        ),
        backstory=(
            "Valenti aveva scoperto ammanchi milionari nella sua fondazione d'arte e falsificazioni "
            "di perizie assicurative. Ha invitato tutti per metterli di fronte a un ultimatum."
        ),
        characteristic_elements=[
            "Linee telefoniche fisse fuori uso dalle 21:05 per il temporale",
            "Passaggio di servizio nascosto dietro la libreria tra Galleria Orientale e Studio Privato",
            "Orologio a pendolo del Salone sincronizzato con il registro del maggiordomo",
        ],
        locations=[
            LocationItem(
                location_id="loc_01",
                name="Studio Privato",
                description="Stanza rivestita in mogano con cassaforte a muro, scrivania e carrello dei liquori.",
                hidden_detail="Una porta a scomparsa dietro gli scaffali conduce alla Galleria Orientale.",
            ),
            LocationItem(
                location_id="loc_02",
                name="Salone delle Feste",
                description="Ampia sala affrescata dove è stato servito l'aperitivo e la cena.",
                hidden_detail="Dal tavolo centrale non si vede chi imbocca il corridoio verso la Galleria.",
            ),
            LocationItem(
                location_id="loc_03",
                name="Veranda sul Lago",
                description="Loggia vetrata affacciata sul pontile in tempesta, con il telefono fisso della villa.",
                hidden_detail="Il telefono fisso è completamente muto dalle 21:05 per la caduta di un traliccio.",
            ),
        ],
        world_secrets=[
            "Solo chi frequentava lo studio da anni conosceva il passaggio dietro la libreria.",
            "La linea telefonica fissa in Veranda era isolata dalle 21:05: chiunque dichiari di aver telefonato dopo quell'ora mente.",
        ],
        public_facts=[
            "Nessuno è entrato o uscito da Villa Morosini dopo le 20:00.",
            "Lorenzo Valenti beveva esclusivamente dal decanter di cristallo inciso nel suo Studio Privato.",
        ],
    )

    secret_solution = SecretSolution(
        victim_name="Lorenzo Valenti",
        culprit_id="char_02",
        culprit_name="Dott. Valerio Santi",
        motive=(
            "Valenti aveva scoperto che il Dott. Santi sottraeva alcaloidi ospedalieri e firmava "
            "false perizie di invalidità e autenticità per coprire debiti di gioco, ed era pronto a denunciarlo lunedì mattina."
        ),
        murder_weapon="Gocce inodori di digossina concentrata versate nel decanter di brandy dello Studio Privato",
        murder_location="Studio Privato",
        time_of_death="21:15 - 21:30",
        opportunity_and_dynamics=(
            "Alle 21:18 il Dott. Santi si è assentato fingendo di andare a telefonare in Veranda; "
            "invece ha usato il passaggio della Galleria Orientale per entrare nello Studio Privato e contaminare il decanter."
        ),
        alibi_flaw=(
            "Dichiara di aver parlato al telefono fisso della Veranda con l'ospedale tra le 21:15 e le 21:25, "
            "ma la linea fissa era interrotta dalle 21:05 e il suo gemello d'argento con iniziali 'V.S.' è stato trovato dietro la libreria dello Studio."
        ),
        deduction_chain=[
            "Indizio clue_01: Il veleno utilizzato (digossina concentrata) richiede accesso medico-farmacologico diretto (punta a char_02).",
            "Indizio clue_02: Il telefono fisso della Veranda era fuori servizio dalle 21:05, smontando l'alibi delle 21:20 di char_02.",
            "Indizio clue_03: Il gemello con iniziali 'V.S.' rinvenuto nel passaggio segreto dello Studio Privato colloca char_02 sulla scena del crimine.",
            "Indizio clue_04: Il dossier disciplinare nella cassaforte di Valenti rivela il movente disperato di char_02.",
        ],
    )

    timeline = [
        TimelineEvent(
            event_id="evt_01",
            timestamp="20:00",
            title="Aperitivo inaugurale e gelo tra gli ospiti",
            description="Lorenzo Valenti accoglie i presenti nel Salone delle Feste annunciando che a fine cena svelerà un tradimento imperdonabile.",
            involved_character_ids=["char_01", "char_02", "char_03", "char_04", "char_05"],
            location="Salone delle Feste",
            is_public=True,
            is_crime_event=False,
        ),
        TimelineEvent(
            event_id="evt_02",
            timestamp="20:45",
            title="Lite riservata tra Elena Morosini e Marco Bellini",
            description="Elena e Marco discutono animatamente in Galleria riguardo alla vendita segreta di una tela fiamminga.",
            involved_character_ids=["char_01", "char_03"],
            location="Galleria Orientale",
            is_public=False,
            is_crime_event=False,
        ),
        TimelineEvent(
            event_id="evt_03",
            timestamp="21:05",
            title="Guasto alla linea telefonica per il nubifragio",
            description="Un fulmine abbatte la linea telefonica fissa della villa; il maggiordomo Arturo Bassi lo annota sul registro di servizio.",
            involved_character_ids=["char_05"],
            location="Veranda sul Lago",
            is_public=False,
            is_crime_event=False,
        ),
        TimelineEvent(
            event_id="evt_04",
            timestamp="21:15 - 21:30",
            title="Avvelenamento nello Studio Privato",
            description="Il Dott. Valerio Santi entra nello Studio Privato dal passaggio della libreria, versa la digossina nel decanter e perde un gemello da polso.",
            involved_character_ids=["char_02"],
            location="Studio Privato",
            is_public=False,
            is_crime_event=True,
        ),
        TimelineEvent(
            event_id="evt_05",
            timestamp="21:45",
            title="Ritrovamento del corpo di Lorenzo Valenti",
            description="Sofia De Luca e Arturo Bassi aprono lo Studio Privato e trovano Valenti privo di vita accanto al calice rovesciato.",
            involved_character_ids=["char_04", "char_05"],
            location="Studio Privato",
            is_public=True,
            is_crime_event=False,
        ),
    ]

    characters = [
        CharacterProfile(
            character_id="char_01",
            name="Contessa Elena Morosini",
            role="Socia della Fondazione Valenti ed ex proprietaria della Villa",
            is_playable=True,
            is_culprit=False,
            background="Aristocratica decaduta che ha ceduto metà della villa a Valenti in cambio di liquidità.",
            personality="Altera, raffinata, ironica ma pronta a difendere con le unghie il prestigio del suo casato.",
            goals=[
                "Impedire che si scopra la sostituzione non autorizzata di una tela fiamminga con una copia",
                "Individuare il vero assassino di Valenti per non perdere i diritti sulla villa",
            ],
            relationships=[
                CharacterRelationship(
                    target_character_id="char_03",
                    target_name="Marco Bellini",
                    relation_type="Complice in affari segreti",
                    public_view="Tratta Marco come un semplice consulente esterno.",
                    hidden_tension="Ha incaricato Marco di vendere di nascosto un dipinto della Fondazione.",
                ),
                CharacterRelationship(
                    target_character_id="char_02",
                    target_name="Dott. Valerio Santi",
                    relation_type="Diffidenza reciproca",
                    public_view="Amici di vecchia data del circolo velico.",
                    hidden_tension="Sospetta che Valerio abbia manipolato le analisi mediche di Valenti.",
                ),
            ],
            secret="Insieme a Marco Bellini ha sostituito un quadro della Fondazione con una copia per saldare un'ipoteca.",
            alibi="Tra le 21:15 e le 21:30 era nella cantina storica con il maggiordomo Arturo Bassi per scegliere il vino del brindisi.",
            motive="Valenti minacciava di estrometterla definitivamente dalla Fondazione Morosini-Valenti.",
            known_facts=[
                "Alle 21:15 era effettivamente con il maggiordomo Arturo Bassi (char_05) in cantina.",
                "Ha notato che al Dott. Valerio Santi mancava il gemello destro della camicia poco prima delle 21:40.",
            ],
            hidden_facts=[
                "Alle 20:45 ha consegnato a Marco Bellini un biglietto urgente per concordare il silenzio sulla tela fiamminga."
            ],
            what_can_reveal="Può rivelare il dettaglio del gemello mancante di Valerio Santi durante la Fase 2.",
            reaction_to_accusation="Risponde con sdegno aristocratico e invoca la testimonianza del maggiordomo sul suo alibi in cantina.",
        ),
        CharacterProfile(
            character_id="char_02",
            name="Dott. Valerio Santi",
            role="Medico personale della vittima e consulente scientifico",
            is_playable=True,
            is_culprit=True,
            background="Cardiologo stimato nell'alta società lariana, ma segretamente schiacciato da debiti e frodi sanitarie.",
            personality="Calmo, metodico, usa un linguaggio tecnico rassicurante per mascherare il nervosismo.",
            goals=[
                "Far credere che il suo alibi telefonico in Veranda sia vero",
                "Indirizzare i sospetti verso Marco Bellini e la Contessa Elena sfruttando il loro litigio delle 20:45",
            ],
            relationships=[
                CharacterRelationship(
                    target_character_id="char_04",
                    target_name="Sofia De Luca",
                    relation_type="Timore giornalistico",
                    public_view="Si mostra cordiale e disponibile con la giornalista.",
                    hidden_tension="Teme che Sofia stia indagando proprio sugli ammanchi della clinica.",
                )
            ],
            secret="È l'assassino di Lorenzo Valenti: ha versato digossina concentrata nel decanter dello Studio Privato alle 21:20.",
            alibi="Sostiene di aver parlato al telefono fisso della Veranda con il primario di guardia tra le 21:15 e le 21:25.",
            motive="Valenti aveva le prove delle sue frodi mediche e stava per consegnarle alla procura.",
            known_facts=[
                "Sa che Marco Bellini ed Elena Morosini litigavano in Galleria alle 20:45.",
                "Conosce l'esistenza del passaggio segreto dietro la libreria dello Studio Privato.",
            ],
            hidden_facts=[
                "Ha perso un gemello d'argento con le iniziali 'V.S.' nel passaggio segreto alle 21:20.",
                "Non sapeva che il telefono fisso della Veranda fosse già muto dalle 21:05.",
            ],
            what_can_reveal="Cerca di spostare l'attenzione sul biglietto minaccioso tra Elena e Marco.",
            reaction_to_accusation="Sostiene che chiunque avrebbe potuto rubargli il gemello o una fiala dalla borsa medica lasciata nell'ingresso.",
        ),
        CharacterProfile(
            character_id="char_03",
            name="Marco Bellini",
            role="Curatore d'arte ed ex braccio destro di Valenti",
            is_playable=True,
            is_culprit=False,
            background="Esperto di pittura antica, licenziato in tronco da Valenti due settimane prima in modo riservato.",
            personality="Passionale, impulsivo, sulla difensiva quando si parla di denaro.",
            goals=[
                "Dimostrare che il suo alterco delle 20:45 riguardava solo un affare d'arte e non l'omicidio",
                "Smascherare il vero colpevole per riabilitare il proprio nome",
            ],
            relationships=[
                CharacterRelationship(
                    target_character_id="char_01",
                    target_name="Contessa Elena Morosini",
                    relation_type="Alleanza segreta",
                    public_view="Collaborazione formale per il catalogo della villa.",
                    hidden_tension="Ha aiutato Elena a piazzare una copia della tela fiamminga.",
                )
            ],
            secret="Ha venduto in segreto l'originale fiammingo per conto della Contessa Elena trattenendo una commissione.",
            alibi="Tra le 21:15 e le 21:30 era nel Salone delle Feste a conversare con la giornalista Sofia De Luca.",
            motive="Valenti aveva scoperto l'ammanco del dipinto e minacciava di rovinarlo professionalmente.",
            known_facts=[
                "Conferma di aver conversato con Sofia De Luca nel Salone delle Feste tra le 21:15 e le 21:30.",
                "Alle 21:18 ha visto il Dott. Santi dirigersi verso la Galleria Orientale e NON verso la Veranda.",
            ],
            hidden_facts=[
                "Il biglietto minaccioso delle 20:45 trovato nel salone era indirizzato a lui da parte di Elena."
            ],
            what_can_reveal="Può testimoniare che alle 21:18 il Dott. Santi camminava verso la Galleria Orientale.",
            reaction_to_accusation="Ammette la questione del quadro se messo alle strette, ma fa notare che Sofia De Luca conferma il suo alibi nell'orario della morte.",
        ),
        CharacterProfile(
            character_id="char_04",
            name="Sofia De Luca",
            role="Giornalista investigativa d'arte e finanza",
            is_playable=True,
            is_culprit=False,
            background="Invitata personalmente da Valenti che voleva affidarle uno scoop esclusivo a fine serata.",
            personality="Acuta, curiosa, prende appunti su tutto e incrocia costantemente orari e dettagli.",
            goals=[
                "Scoprire quale dossier Valenti voleva consegnarle",
                "Risolvere il caso prima dell'arrivo della polizia",
            ],
            relationships=[
                CharacterRelationship(
                    target_character_id="char_03",
                    target_name="Marco Bellini",
                    relation_type="Testimone d'alibi",
                    public_view="Intervistatrice interessata al mercato dell'arte.",
                    hidden_tension="Sa che Marco nasconde qualcosa sui quadri, ma può confermare che era con lei durante l'omicidio.",
                )
            ],
            secret="Aveva installato un piccolo registratore vocale nella borsa per documentare le rivelazioni della serata.",
            alibi="Tra le 21:15 e le 21:30 era nel Salone delle Feste a interrogare Marco Bellini.",
            motive="Un anno fa Valenti aveva fatto bloccare una sua inchiesta giornalistica con una querela milionaria.",
            known_facts=[
                "Conferma l'alibi di Marco Bellini tra le 21:15 e le 21:30 nel Salone delle Feste.",
                "Alle 21:08 ha provato a usare il telefono fisso della Veranda, scoprendo che la linea era completamente muta.",
            ],
            hidden_facts=[
                "Valenti le aveva anticipato che il dossier più grave riguardava 'un medico che gioca con la vita e con i veleni'."
            ],
            what_can_reveal="Può svelare subito che il telefono fisso della Veranda era fuori uso già alle 21:08!",
            reaction_to_accusation="Mostra i suoi appunti orari e ricorda che non avrebbe mai ucciso la sua fonte prima di ricevere i documenti.",
        ),
        CharacterProfile(
            character_id="char_05",
            name="Arturo Bassi",
            role="Maggiordomo storico di Villa Morosini",
            is_playable=False,
            is_culprit=False,
            background="Al servizio della villa da trent'anni, conosce ogni corridoio e osserva i segreti degli ospiti in silenzio.",
            personality="Impassibile, preciso sugli orari, devoto alla memoria della villa.",
            goals=[
                "Fornire riscontri oggettivi sugli orari della serata",
                "Assicurare che il colpevole venga consegnato alla giustizia",
            ],
            relationships=[
                CharacterRelationship(
                    target_character_id="char_01",
                    target_name="Contessa Elena Morosini",
                    relation_type="Fedeltà storica",
                    public_view="Servitore impeccabile.",
                    hidden_tension="Conferma l'alibi di Elena in cantina tra le 21:15 e le 21:30.",
                )
            ],
            secret="Sapeva che Valenti aveva cambiato la combinazione della cassaforte quello stesso pomeriggio.",
            alibi="Tra le 21:15 e le 21:30 era in cantina con la Contessa Elena Morosini.",
            motive="Valenti aveva annunciato il taglio del personale storico della tenuta.",
            known_facts=[
                "Ha annotato sul registro che la linea telefonica fissa è saltata alle 21:05.",
                "Conferma che la Contessa Elena era con lui in cantina durante la finestra del delitto.",
            ],
            hidden_facts=[
                "Ha trovato una fiala vuota senza etichetta nel cestino di servizio vicino alla Galleria Orientale."
            ],
            what_can_reveal="Conferma gli orari del registro di servizio e l'interruzione telefonica delle 21:05.",
            reaction_to_accusation="Esibisce il registro di servizio firmato e la testimonianza congiunta della Contessa.",
        ),
    ]

    subplots = [
        SubplotItem(
            subplot_id="sub_01",
            title="Il Falso Fiammingo della Fondazione",
            category="Interesse economico / Segreto d'arte",
            involved_character_ids=["char_01", "char_03"],
            description=(
                "La Contessa Elena Morosini e Marco Bellini hanno sostituito una tela del Seicento "
                "con una copia perfetta per estinguere un debito urgente."
            ),
            player_triggers="Il ritrovamento del biglietto strappato ('clue_05') spinge gli altri a interrogare Elena e Marco sul loro incontro delle 20:45.",
            resolution=(
                "Se Elena e Marco ammettono che il loro incontro delle 20:45 riguardava solo il dipinto, "
                "possono unire i loro alibi (confermati da Arturo e Sofia) e scagionarsi dall'accusa di omicidio."
            ),
            connects_to_main_plot="Costituisce il principale depistaggio iniziale della serata.",
        ),
        SubplotItem(
            subplot_id="sub_02",
            title="Lo Scoop Insabbiato di Sofia De Luca",
            category="Conflitto professionale / Inchiesta",
            involved_character_ids=["char_04", "char_02"],
            description=(
                "Sofia De Luca sta indagando su un traffico di farmaci ospedalieri e perizie truccate "
                "che porta dritto alla clinica del Dott. Valerio Santi."
            ),
            player_triggers="Gli appunti investigativi di Sofia coincidono con il dossier trovato nello Studio Privato.",
            resolution="Sofia collega l'indizio farmacologico alle attività illecite del Dott. Santi.",
            connects_to_main_plot="Rafforza la prova del movente e dell'accesso al veleno da parte di char_02.",
        ),
    ]

    clues = [
        ClueItem(
            clue_id="clue_01",
            title="Fiala di Digossina e Calice di Cristallo",
            clue_type="fisico",
            description="Nel cestino vicino alla Galleria Orientale è stata trovata una micro-fiala ospedaliera di digossina concentrata; tracce identiche sono nel decanter.",
            printable_text=(
                "[REPERTO #01 — ANALISI SCENA DEL CRIMine]\n"
                "Il brandy nel decanter personale di Lorenzo Valenti contiene un'alta concentrazione di digossina "
                "pura per uso ospedaliero. Una micro-fiala con lotto clinico riservato è stata gettata vicino alla Galleria Orientale."
            ),
            discovery_phase=1,
            location_or_holder="Studio Privato / Galleria Orientale",
            points_to_character_id="char_02",
            contradicts_alibi_of_id=None,
            is_red_herring=False,
            logical_inference="L'assassino possiede competenze mediche e accesso diretto a farmaci ospedalieri (char_02).",
        ),
        ClueItem(
            clue_id="clue_02",
            title="Registro Guasti: Linea Telefonica Isolata dalle 21:05",
            clue_type="contraddizione",
            description="Il registro del maggiordomo e la verifica tecnica confermano che il telefono fisso della Veranda è muto dalle 21:05.",
            printable_text=(
                "[REPERTO #02 — REGISTRO DI SERVIZIO DELLA VILLA]\n"
                "Ore 21:05: Un fulmine ha tranciato il cavo telefonico esterno. Il telefono fisso della Veranda "
                "sul Lago è completamente fuori servizio dalle 21:05 in poi."
            ),
            discovery_phase=2,
            location_or_holder="Veranda sul Lago",
            points_to_character_id="char_02",
            contradicts_alibi_of_id="char_02",
            is_red_herring=False,
            logical_inference="Smentisce categoricamente l'alibi del Dott. Valerio Santi (char_02), che sostiene di aver telefonato dalla Veranda alle 21:20.",
        ),
        ClueItem(
            clue_id="clue_03",
            title="Gemello d'Argento con Iniziali 'V.S.' nel Passaggio Segreto",
            clue_type="oggetto",
            description="Dietro la libreria girevole dello Studio Privato è rimasto impigliato un gemello da polso in argento inciso 'V.S.'.",
            printable_text=(
                "[REPERTO #03 — OGGETTO PERSONALE RINVENUTO]\n"
                "Sul pavimento del passaggio segreto che collega la Galleria Orientale allo Studio Privato "
                "è stato rinvenuto un gemello da polso in argento con le iniziali 'V.S.' e il fermaglio spezzato."
            ),
            discovery_phase=2,
            location_or_holder="Passaggio segreto dietro la libreria",
            points_to_character_id="char_02",
            contradicts_alibi_of_id="char_02",
            is_red_herring=False,
            logical_inference="Prova fisica che Valerio Santi (char_02) ha usato il passaggio segreto per entrare nello Studio Privato.",
        ),
        ClueItem(
            clue_id="clue_04",
            title="Dossier 'Clinica San Giorgio' nella Cassaforte",
            clue_type="documento",
            description="Fascicolo riservato di Valenti con le prove delle perizie mediche falsificate dal Dott. Valerio Santi.",
            printable_text=(
                "[REPERTO #04 — DOSSIER RISERVATO DELLA VITTIMA]\n"
                "Appunto autografo di Lorenzo Valenti: 'Ho le prove firmate delle false perizie e della sottrazione "
                "di farmaci da parte del Dott. Valerio Santi. Lunedì mattina consegnerò tutto al Procuratore.'"
            ),
            discovery_phase=3,
            location_or_holder="Cassaforte dello Studio Privato",
            points_to_character_id="char_02",
            contradicts_alibi_of_id="char_02",
            is_red_herring=False,
            logical_inference="Conferma il movente diretto e urgente di char_02 per uccidere Valenti quella sera stessa.",
        ),
        ClueItem(
            clue_id="clue_05",
            title="Biglietto Strappato dell'Appuntamento delle 20:45",
            clue_type="messaggio",
            description="Biglietto urgente scritto dalla Contessa Elena a Marco Bellini riguardo al quadro fiammingo.",
            printable_text=(
                "[REPERTO #05 — BIGLIETTO STRAPPATO]\n"
                "'Marco, vediamoci in Galleria alle 20:45. Se Lorenzo scopre la sostituzione prima di domani, siamo rovinati entrambi.'"
            ),
            discovery_phase=1,
            location_or_holder="Salone delle Feste",
            points_to_character_id="char_03",
            contradicts_alibi_of_id=None,
            is_red_herring=True,
            logical_inference="Depistaggio legato alla sottotrama sub_01: riguarda il furto del quadro alle 20:45, non l'omicidio delle 21:20.",
        ),
    ]

    gameplay = GameplayStructure(
        phases=[
            GamePhase(
                phase_number=1,
                title="Fase 1: Il Brindisi Interrotto e i Primi Sospetti",
                duration_minutes=30,
                objectives=[
                    "Presentazione pubblica di tutti i personaggi",
                    "Raccolta degli alibi iniziali per la fascia 21:15 - 21:30",
                    "Analisi dei Reperti #01 e #05",
                ],
                revealed_clue_ids=["clue_01", "clue_05"],
                scheduled_events=[
                    "Lettura del Prologo Drammatico",
                    "Apertura Busta Indizi Fase 1",
                ],
                interrogation_mechanics="Conversazioni libere ai tavoli e prime domande sugli spostamenti tra le 20:45 e le 21:30.",
            ),
            GamePhase(
                phase_number=2,
                title="Fase 2: Alibi in Frantumi e Passaggi Segreti",
                duration_minutes=35,
                objectives=[
                    "Smontare l'alibi telefonico grazie al Reperto #02",
                    "Scoprire il legame del gemello 'V.S.' (Reperto #03)",
                    "Risolvere la sottotrama del falso fiammingo tra Elena e Marco",
                ],
                revealed_clue_ids=["clue_02", "clue_03"],
                scheduled_events=[
                    "Consegna delle Buste Riservate di metà serata",
                    "Apertura Busta Indizi Fase 2",
                ],
                interrogation_mechanics="Giro di interrogatori incrociati: ogni giocatore pone una domanda diretta a cui il destinatario deve rispondere davanti a tutti.",
            ),
            GamePhase(
                phase_number=3,
                title="Fase 3: La Cassaforte Aperta e le Accuse Finali",
                duration_minutes=25,
                objectives=[
                    "Esaminare il Dossier della Cassaforte (Reperto #04)",
                    "Ricostruire la catena completa (Chi, Come, Quando, Perché, Falla nell'alibi)",
                    "Compilare le schede di accusa e ascoltare la Rivelazione Finale",
                ],
                revealed_clue_ids=["clue_04"],
                scheduled_events=[
                    "Apertura della Cassaforte (Indizio clue_04)",
                    "Consegna delle Schede d'Accusa e Lettura della Soluzione",
                ],
                interrogation_mechanics="Arringa finale di 2 minuti per ciascun sospettato prima del voto segreto.",
            ),
        ],
        information_distribution_rules=(
            "Ogni giocatore riceve solo la propria scheda personale. Gli indizi sono divisi in 3 buste numerate "
            "che il Master apre all'inizio di ciascuna fase."
        ),
        accusation_mechanics=(
            "Ogni giocatore scrive sulla scheda finale: 1) Nome del Colpevole, 2) Arma e Luogo, "
            "3) Movente, 4) Quale prova smentisce il suo alibi."
        ),
        victory_conditions=(
            "Vince il titolo di Miglior Investigatore chi totalizza più punti individuando colpevole (+3), "
            "movente (+2), falla nell'alibi (+2) e proteggendo il proprio segreto (+2)."
        ),
        master_notes=(
            "Nella Fase 1 lascia che i giocatori sospettino di Marco ed Elena per via del biglietto delle 20:45; "
            "nella Fase 2 fai notare l'orario del guasto telefonico delle 21:05."
        ),
    )

    narrative = NarrativeMaterials(
        introduction_md=(
            "# Benvenuti a Villa Morosini\n\n"
            "Fuori il Lago di Como è sferzato dal vento e dai lampi; dentro, tra i velluti cremisi del Salone delle Feste, "
            "Lorenzo Valenti aveva promesso un annuncio destinato a cambiare per sempre le vostre vite. "
            "Ma alle 21:45 la porta dello Studio Privato è stata forzata e il padrone di casa giaceva accanto a un calice infranto."
        ),
        prologue_speech_md=(
            "«Signore e signori, nessuno lasci la sala. Il temporale ha isolato Villa Morosini e la linea telefonica è muta. "
            "Lorenzo Valenti non è morto per cause naturali: qualcuno tra voi è entrato nel suo Studio Privato tra le 21:15 e le 21:30 "
            "e ha versato un veleno letale nel suo decanter. Guardatevi negli occhi: l'assassino siede a questo stesso tavolo.»"
        ),
        character_dialogues={
            "char_01": [
                "«Io avvelenare Lorenzo? Assurdo: alle 21:20 ero in cantina con il maggiordomo Arturo a scegliere il rincalzo d'annata.»",
                "«Chiedete piuttosto al Dottor Santi come mai gli manca un gemello dal polsino destro!»",
            ],
            "char_02": [
                "«Come medico posso assicurarvi che si tratta di una sostanza complessa; io alle 21:20 ero in Veranda per una chiamata urgente.»",
                "«Non dimentichiamo che Marco Bellini ed Elena Morosini litigavano furiosamente in Galleria poco prima!»",
            ],
            "char_03": [
                "«Sì, avevo conti in sospeso con Lorenzo, ma tra le 21:15 e le 21:30 ero qui nel Salone con Sofia De Luca!»",
                "«E alle 21:18 ho visto con i miei occhi il Dottor Santi imboccare la Galleria Orientale, altro che Veranda!»",
            ],
            "char_04": [
                "«Da giornalista mi fido solo dei fatti: Marco Bellini era con me nel Salone dalle 21:15 alle 21:30.»",
                "«E c'è di più: alle 21:08 ho provato a telefonare dalla Veranda e la linea era già completamente morta!»",
            ],
            "char_05": [
                "«Il mio registro non mente mai: il fulmine ha isolato il telefono fisso alle 21:05 in punto.»",
                "«Posso confermare che la Contessa Morosini si trovava con me nella cantina storica tra le 21:15 e le 21:30.»",
            ],
        },
        confidential_communications={
            "char_01": "Busta Riservata Fase 2: Hai ricordato che al Dott. Santi mancava il gemello destro quando è rientrato nel Salone alle 21:35.",
            "char_02": "Busta Riservata Fase 2: Attenzione! Qualcuno ha scoperto che il telefono della Veranda era guasto. Se ti incalzano, sostieni di aver provato a comporre il numero senza riuscirci.",
            "char_03": "Busta Riservata Fase 2: Ricorda a tutti che alle 21:18 hai visto il Dott. Santi dirigersi verso la Galleria Orientale.",
            "char_04": "Busta Riservata Fase 2: Usa l'informazione sul telefono guasto delle 21:08 per verificare chi sta mentendo sul proprio alibi.",
            "char_05": "Busta Riservata Fase 2: Mostra agli investigatori l'annotazione delle 21:05 sul guasto della linea fissa.",
        },
        documents=[
            InGameDocument(
                doc_id="doc_01",
                doc_type="letter",
                title="Lettera Riservata di Lorenzo Valenti al Procuratore",
                sender="Lorenzo Valenti",
                recipient="Procura della Repubblica di Como",
                content=(
                    "Ill.mo Procuratore, Le trasmetto in allegato la documentazione sulle false perizie mediche "
                    "e sugli ammanchi di alcaloidi ospedalieri riconducibili al Dott. Valerio Santi."
                ),
                related_clue_id="clue_04",
            ),
            InGameDocument(
                doc_id="doc_02",
                doc_type="message",
                title="Biglietto Manoscritto tra Elena e Marco",
                sender="Contessa Elena Morosini",
                recipient="Marco Bellini",
                content="Marco, vediamoci in Galleria alle 20:45. Nessuno deve sapere della sostituzione della tela fiamminga.",
                related_clue_id="clue_05",
            ),
            InGameDocument(
                doc_id="doc_03",
                doc_type="evidence",
                title="Estratto del Registro di Servizio del Maggiordomo",
                sender="Arturo Bassi (Maggiordomo)",
                recipient="Archivio Villa Morosini",
                content=(
                    "20:00 - Inizio aperitivo nel Salone.\n"
                    "21:05 - Guasto totale alla linea telefonica fissa in Veranda causa temporale.\n"
                    "21:15-21:30 - Ispezione cantina vini con la Contessa Morosini.\n"
                    "21:45 - Rinvenimento del corpo nello Studio Privato."
                ),
                related_clue_id="clue_02",
            ),
        ],
    )

    project = MysteryProject(
        project_id="mm_demo_villa_morosini",
        status="completed",
        current_phase="Fase 10 – Finalization",
        config=config,
        concept=concept,
        world=world,
        plot=MainPlot(
            crime_overview=concept.crime_summary,
            secret_solution=secret_solution,
            timeline=timeline,
            red_herrings=[
                "Il litigio delle 20:45 tra Elena Morosini e Marco Bellini per il falso quadro fiammingo",
                "La vecchia querela milionaria di Valenti contro la giornalista Sofia De Luca",
            ],
            alternative_developments=[
                "Se il Dott. Santi viene smascherato nella Fase 2, tenta di accusare Marco Bellini di avergli sottratto la fiala dalla borsa medica."
            ],
        ),
        characters=characters,
        subplots=subplots,
        clues=clues,
        gameplay=gameplay,
        narrative=narrative,
        reviews=[
            ReviewReport(
                iteration=1,
                passed=True,
                coherence_score=96,
                critiques=[],
                summary="Grafo narrativo completamente coerente: alibi incrociati verificati, 4 prove convergenti su char_02 e 1 depistaggio risolubile.",
            )
        ],
    )

    InformationGraphValidator.synchronize_canonical_graph(project)

    # Populate agent activity logs for Control Room observability
    project.log_activity("Fase 1 – Concept", "GameDirector", "generate_concept", f"Concept '{concept.title}' definito.")
    project.log_activity("Fase 2 – World Building", "WorldBuilder", "generate_world", "Ambientazione Villa Morosini e 3 luoghi chiave creati.")
    project.log_activity("Fase 3 – Plot Design", "PlotArchitect", "generate_plot", "Soluzione segreta (colpevole char_02) e timeline in 5 eventi definite.")
    project.log_activity("Fase 4 – Character Design", "CharacterDesigner", "generate_characters", "Creati 4 personaggi giocanti e 1 PNG con segreti e alibi.")
    project.log_activity("Fase 5 – Subplot Design", "SubplotDesigner", "generate_subplots", "Create 2 sottotrame intrecciate (Falso Fiammingo e Inchiesta Clinica).")
    project.log_activity("Fase 6 – Clue Design", "ClueMaster", "generate_clues", "Creati 5 indizi (4 prove canoniche + 1 depistaggio).")
    project.log_activity("Fase 7 – Game Design", "GameMechanicsDesigner", "generate_gameplay", "Strutturate 3 fasi di gioco da 90 minuti complessivi.")
    project.log_activity("Fase 8 – Narrative Production", "NarrativeWriter", "generate_narrative", "Scritti prologo, dialoghi e 3 documenti in-game.")
    project.log_activity("Fase 9 – Critical Review", "ContinuityEditor", "review_iteration_1", "Revisione superata con punteggio 96/100 (0 contraddizioni).")

    # Assemble final production markdown documents using FinalGameProducer formatting
    timeline_md = "\n".join(
        f"- **{e.timestamp}** (`{e.event_id}`) — **{e.title}** [{e.location}]: {e.description}"
        for e in project.plot.timeline
    )
    phases_md = "\n\n".join(
        f"### Fase {p.phase_number}: {p.title} ({p.duration_minutes} min)\n"
        f"- **Obiettivi**: {'; '.join(p.objectives)}\n"
        f"- **Indizi Rivelati**: {', '.join(p.revealed_clue_ids)}\n"
        f"- **Meccanica**: {p.interrogation_mechanics}"
        for p in project.gameplay.phases
    )
    project.final_production = FinalProductionSuite(
        master_manual_md=(
            f"# Manuale del Master — {concept.title}\n\n"
            f"> **DOCUMENTO RISERVATO AL MASTER — NON MOSTRARE AI GIOCATORI**\n\n"
            f"## 1. Sintesi Esecutiva\n{concept.hook}\n\n"
            f"## 2. Regia delle Fasi\n{phases_md}\n\n"
            f"## 3. Cronologia Canonica\n{timeline_md}\n\n"
            f"## 4. Note di Regia\n{gameplay.master_notes}\n"
        ),
        player_instructions_md=(
            f"# Regole e Istruzioni per i Giocatori — {concept.title}\n\n"
            f"{narrative.introduction_md}\n\n"
            f"## Regole d'Indagine\n{gameplay.information_distribution_rules}\n\n"
            f"## Accusa Finale\n{gameplay.accusation_mechanics}\n\n"
            f"## Condizioni di Vittoria\n{gameplay.victory_conditions}\n"
        ),
        secret_resolution_md=(
            f"# SOLUZIONE SEGRETA DEL MASTER — {concept.title}\n\n"
            f"- **Colpevole**: **{secret_solution.culprit_name}** (`{secret_solution.culprit_id}`)\n"
            f"- **Arma**: {secret_solution.murder_weapon}\n"
            f"- **Luogo e Ora**: {secret_solution.murder_location} ({secret_solution.time_of_death})\n"
            f"- **Movente**: {secret_solution.motive}\n"
            f"- **Falla nell'Alibi**: {secret_solution.alibi_flaw}\n\n"
            f"## Catena Deduttiva\n" + "\n".join(f"- {s}" for s in secret_solution.deduction_chain)
        ),
        master_report_md=(
            f"# Master Report — {concept.title}\n\n"
            f"Punteggio Coerenza Continuity Editor: **96/100**\n\n"
            + "\n".join(
                f"- **{c.character_id} ({c.name})**: {'COLPEVOLE' if c.is_culprit else 'Innocente'} | Alibi: {c.alibi}"
                for c in project.characters
            )
        ),
        complete_story_md=(
            f"# Storia Completa — {concept.title}\n\n"
            f"{narrative.introduction_md}\n\n"
            f"## Prologo\n{narrative.prologue_speech_md}\n\n"
            f"## Cronologia\n{timeline_md}\n"
        ),
    )
    project.log_activity("Fase 10 – Finalization", "FinalGameProducer", "finalize_production_suite", "Dossier completo generato e pronto all'esportazione.")
    return project
