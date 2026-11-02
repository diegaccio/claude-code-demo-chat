"""Every user-visible text of the Demo app, in Italian."""

APP_TITLE = "Demo app"
WORDMARK = "Base Digitale"
PROMPT_PLACEHOLDER = "Scrivi un messaggio e premi Invio"
USER_TURN = "Tu: {text}"

PROFILE_NAMES = {"local": "locale", "srh": "SRH"}
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
SRH_URL_MISSING = (
    "L'indirizzo del server SRH non è configurato. "
    "Impostalo nel file .env (SRH_BASE_URL) e riavvia l'app."
)
