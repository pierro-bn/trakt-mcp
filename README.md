# trakt-mcp

[![Soutenir sur Ko-fi](https://img.shields.io/badge/Ko--fi-Soutenir%20le%20projet-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/pierrobn)

Serveur MCP pour explorer les films et séries et accéder aux données de votre compte Trakt. Dérivé communautaire de [wwiens/trakt_mcpserver](https://github.com/wwiens/trakt_mcpserver), sous licence MIT ; les attributions d'origine sont conservées.

## Installation

Prérequis pour utiliser le serveur : **Python 3.12 ou plus récent**.

```sh
git clone https://github.com/pierro-bn/trakt-mcp.git
cd trakt-mcp
python -m venv .venv
```

Activez l'environnement avec `.venv\Scripts\Activate.ps1` sous PowerShell ou `source .venv/bin/activate` sous macOS/Linux, puis :

```sh
python -m pip install -e .
```

Configurez votre client MCP pour lancer l'exécutable installé `trakt-mcp` sur **stdio**, avec `TRAKT_CLIENT_ID` dans son environnement.

| Variable | Utilisation |
| --- | --- |
| `TRAKT_CLIENT_ID` | Client ID de votre application Trakt |
| `TRAKT_CLIENT_SECRET` | Facultatif ; omis pour la connexion habituelle par code d'appareil, accepté au rafraîchissement s'il est configuré |
| `TRAKT_AUTH_TOKEN_PATH` | Chemin local du jeton ; par défaut `~/.trakt-mcp/auth_token.json` |

## Fonctionnalités et connexion

Recherche de films et séries, tendances, fiches, saisons, épisodes, personnes et commentaires ; historique personnel, notes, watchlist, progression et recommandations.

Depuis l'assistant connecté, appelez `start_device_auth`, ouvrez le lien fourni et saisissez le code. Une fois l'autorisation terminée, appelez `check_auth_status`. `clear_auth` supprime la connexion locale.

**Ce serveur peut modifier le compte** : historique, notes, watchlist, check-ins, recommandations masquées et progression de lecture. Il demande à l'assistant d'obtenir une confirmation avant les changements ; il ne possède pas le mécanisme d'aperçu/jeton de validation de TIDAL. Réglez les autorisations d'outils dans votre client selon vos besoins.

Exemple : « Consulte mes films vus et propose cinq films que je n'ai pas encore regardés. »

## Réponses compactes et économie de tokens

Les outils `search_movies`, `search_shows`, `fetch_user_watched_movies` et `fetch_user_watched_shows` acceptent `detail: "compact"` (par défaut) ou `detail: "detailed"`. Le mode compact renvoie du JSON avec les IDs Trakt, titres, années et les métadonnées de pagination ou de couverture disponibles. Les synopsis restent accessibles en mode détaillé. Les conseils répétés sous chaque résultat de recherche ont été supprimés. Les ressources MCP et les autres outils conservent leur format existant.

`check_watched` prend `media_type` (`movies` ou `shows`) et `ids` (1 à 100 IDs Trakt). Il compare les candidats aux données de l'endpoint watched, sans appliquer la limite d'affichage des listes. Les états sont `watched`, `not_watched` et `unknown`, accompagnés de `complete` et `reason`. Une erreur, une authentification absente ou des identifiants manquants ne sont pas traités comme une absence. Pour une série, `watched` signifie au moins un épisode vu, pas nécessairement la série terminée.

Exemple : `{"media_type":"movies","ids":[1,2]}`. Les outils d'écriture restent inchangés.

Les gains dépendent de la taille des résultats et du client MCP ; ce mode ne garantit pas un pourcentage de réduction des tokens.

## Développement

Les tests demandent aussi **Node.js 22 ou plus récent** pour le MCP Inspector :

```sh
python -m pip install -r requirements-dev.txt
npm ci --ignore-scripts
python -m pytest
```

Node.js est requis pour cette suite de vérification, pas pour exécuter le serveur Python.

## Confidentialité

Ne commitez pas vos clés, jetons, fichiers de session ou exports personnels. Les outils peuvent renvoyer des données du compte connecté au client MCP ; vérifiez ces résultats avant de les partager.

## Changes in this derivative

Structured log fields recursively redact common credential keys without mutating the original request data. Regression tests cover nested headers and token fields.

Cette version est distribuée sous forme de sources sur GitHub, sans publication npm ou PyPI.

## Claude et ChatGPT

| Client | Connexion proposée |
| --- | --- |
| Claude Desktop | Serveur local MCP sur stdio, configuration ci-dessous |
| Claude Code | Même commande locale, via `claude mcp add` |
| ChatGPT | Serveur local relié par Secure MCP Tunnel, sous réserve d'accès à cette fonction |
| Claude web / mobile | Non fourni ici : exige un serveur MCP distant accessible en HTTPS |

Le dépôt GitHub contient le code, pas un endpoint MCP hébergé. Les tests vérifient l'initialisation et la découverte des outils sur stdio ; ils ne constituent pas une connexion réelle à ton compte Claude ou ChatGPT.

### Claude Desktop

Installe d'abord le projet avec les commandes ci-dessus. Ouvre la configuration MCP de Claude Desktop (`claude_desktop_config.json`) et fusionne cette entrée avec tes serveurs existants :

```json
{
  "mcpServers": {
    "trakt-mcp": {
      "command": "C:/mcp/trakt-mcp/.venv/Scripts/python.exe",
      "args": [
        "C:/mcp/trakt-mcp/server.py"
      ],
      "env": {
        "TRAKT_CLIENT_ID": "REPLACE_LOCALLY"
      }
    }
  }
}
```

Un [fichier exemple](examples/claude_desktop_config.example.json) est fourni. Remplace les chemins génériques et les valeurs `REPLACE_…` uniquement dans ta configuration privée. Sous macOS/Linux, utilise le chemin absolu du dépôt et `.venv/bin/python` à la place de `.venv/Scripts/python.exe`. Aucun terminal interactif ne doit être nécessaire au démarrage. Redémarre Claude après modification.

### Claude Code

Après avoir défini les mêmes variables d'environnement dans ton terminal, enregistre la commande avec une portée utilisateur :

```sh
claude mcp add --transport stdio --scope user trakt-mcp -- "C:/mcp/trakt-mcp/.venv/Scripts/python.exe" "C:/mcp/trakt-mcp/server.py"
```

Adapte les chemins à ton système ; consulte `claude mcp list`, puis `/mcp` dans Claude Code pour vérifier la connexion. Les secrets du terminal doivent être disponibles lors des lancements suivants ; une configuration d'environnement privée persistante peut être nécessaire.

### ChatGPT — tunnel privé

Installe [tunnel-client](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), crée un tunnel autorisé pour ton espace et définis localement `CONTROL_PLANE_API_KEY`, ainsi que les variables du serveur.

```sh
tunnel-client init --sample sample_mcp_stdio_local --profile trakt-mcp --tunnel-id REPLACE_WITH_TUNNEL_ID --mcp-command "C:/mcp/trakt-mcp/.venv/Scripts/trakt-mcp.exe"
tunnel-client doctor --profile trakt-mcp --explain
tunnel-client run --profile trakt-mcp
```

Garde ce processus ouvert. Dans ChatGPT : **Plugins → Ajouter un serveur MCP personnalisé → Tunnel**, sélectionne ce tunnel, puis installe le plugin. Ce serveur local ne fournit pas OAuth côté MCP : choisis « Sans authentification » pour cette connexion privée protégée par les droits du tunnel. L'authentification du service reste locale. L'accès dépend des permissions de ton organisation/espace. [Guide officiel](https://developers.openai.com/api/docs/guides/custom-mcp-server).

Les commandes ci-dessus supposent des chemins sans espaces pour la commande encapsulée par le tunnel. Adapte-les ou configure le lancement selon l'aide de `tunnel-client`. Sous macOS/Linux, remplace l'exécutable Python installé par `.venv/bin/trakt-mcp`. Le tunnel donne accès au compte configuré sur cette machine : réserve-le à ton espace de confiance. Il ne transforme pas ce serveur personnel en service multi-utilisateur.

### Session et authentification

Renseigne uniquement `TRAKT_CLIENT_ID` pour la configuration habituelle. Utilise `start_device_auth`, suis le lien et le code de connexion, puis appelle `check_auth_status`. Ce serveur utilise le flux par code d'appareil, pas PKCE. Le serveur conserve le jeton localement ; `clear_auth` supprime la connexion locale. Ne colle jamais les jetons dans une conversation.

Trakt recommande PKCE pour le flux OAuth avec redirection et indique que le Client Secret est déprécié pour la connexion utilisateur : [documentation officielle](https://developer.trakt.tv/docs/authentication-oauth). Cela ne rend pas `TRAKT_CLIENT_SECRET` obligatoire pour le flux par code d'appareil implémenté ici.

### Vérification et dépannage

Essaie : « Vérifie mon authentification Trakt avec check_auth_status. » Les résultats des outils et ressources peuvent contenir des données de ton compte ; le client qui les consulte les reçoit. Si le serveur ne démarre pas, vérifie les chemins absolus, l'installation des dépendances et les variables d'environnement. Si ChatGPT ne propose pas ton tunnel, vérifie ses droits et son rattachement à l'espace. Ne renseigne pas l'URL GitHub comme URL de serveur MCP.

Références : [Claude local](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop), [Claude Code MCP](https://code.claude.com/docs/en/mcp), [connecteurs Claude distants](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp). Voir ces guides pour les réglages propres à chaque client.

## Soutenir le projet

Si ce serveur MCP vous est utile, vous pouvez soutenir son développement et sa maintenance avec un don facultatif sur [Ko-fi](https://ko-fi.com/pierrobn). Merci pour votre soutien !
