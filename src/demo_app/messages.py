"""Every user-visible text of the Demo app, in Italian."""

APP_TITLE = "Demo app"
WORDMARK = "Base Digitale"
PROMPT_PLACEHOLDER = "Scrivi un messaggio e premi Invio"
USER_TURN = "Tu: {text}"

PROFILE_NAMES = {"local": "locale"}
STATUS_PROFILE = "Profilo: {profile} · {model}"

MODEL_UNREACHABLE = (
    "Impossibile raggiungere il server del modello. "
    "Controlla che sia avviato e riprova."
)
MODEL_MISSING = (
    "Il modello «{model}» non è disponibile sul server. "
    "Controlla il nome del modello nelle impostazioni, "
    "oppure scaricalo sul server, e riprova."
)
MODEL_ERROR = "Il server del modello ha risposto con un errore. Riprova tra poco."

PERSONAS = {
    "pirata": "Sei un pirata allegro: rispondi sempre in italiano, con modi di dire da mare aperto.",
    "professore": "Sei un professore paziente: rispondi sempre in italiano, spiegando ogni cosa passo dopo passo.",
    "poeta": "Sei un poeta: rispondi sempre in italiano, in versi brevi e rimati.",
}
PERSONA_SWITCHED = "Persona attiva: {name}."
PERSONA_UNKNOWN = "Persona non trovata. Persone disponibili: {names}."
PERSONA_USAGE = "Uso: /persona <nome>. Persone disponibili: {names}."
CONVERSATION_SAVED = "Conversazione salvata come «{name}»."
CONVERSATION_LOADED = "Conversazione «{name}» caricata. Puoi continuare da qui."
CONVERSATION_MISSING = (
    "Non esiste nessuna conversazione salvata chiamata «{name}». "
    "Controlla il nome e riprova."
)
CONVERSATION_CORRUPT = (
    "Non riesco a leggere la conversazione «{name}»: il file è danneggiato."
)
CONVERSATION_NAME_INVALID = (
    "Il nome può contenere solo lettere, numeri, trattini e trattini bassi."
)
CONVERSATION_NAME_USAGE = "Indica un nome: /save <nome> oppure /load <nome>."
