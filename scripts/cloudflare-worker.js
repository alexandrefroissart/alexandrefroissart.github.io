/**
 * Cloudflare Worker - Proxy API Root-Me
 * 
 * Ce worker fait office de proxy entre ton site et l'API Root-Me.
 * La clé API est stockée de manière sécurisée dans les variables d'environnement.
 * 
 * Déploiement :
 * 1. Créer un compte Cloudflare (gratuit) : https://dash.cloudflare.com/sign-up
 * 2. Aller dans Workers & Pages > Create Worker
 * 3. Coller ce code et cliquer "Deploy"
 * 4. Aller dans Settings > Variables > Add variable
 *    - Nom: ROOTME_API_KEY
 *    - Valeur: 1071705_b1a923c6f19edcb89aa15bee046a6fe745144f36dbb24c316752ee391fc1a958
 *    - Cocher "Encrypt"
 * 5. Noter l'URL du worker (ex: rootme-proxy.votre-nom.workers.dev)
 */

export default {
    async fetch(request, env) {
        // CORS headers pour permettre les appels depuis ton site
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        };

        // Gérer les requêtes OPTIONS (preflight CORS)
        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        // Récupérer l'UID depuis l'URL (ex: /auteurs/1071705)
        const url = new URL(request.url);
        const pathMatch = url.pathname.match(/\/auteurs\/(\d+)/);

        if (!pathMatch) {
            return new Response(JSON.stringify({ error: 'Format: /auteurs/{uid}' }), {
                status: 400,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }

        const uid = pathMatch[1];
        const apiUrl = `https://api.www.root-me.org/auteurs/${uid}`;

        try {
            // Appel à l'API Root-Me avec la clé API
            const response = await fetch(apiUrl, {
                headers: {
                    'Cookie': `api_key=${env.ROOTME_API_KEY}`
                }
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}`);
            }

            const data = await response.json();

            // Formater les données pour le frontend
            const profile = {
                nom: data.nom || 'Unknown',
                score: data.score || 0,
                position: data.position || 0,
                challenges_resolus: data.challenges ? data.challenges.length : 0,
                profil_url: `https://www.root-me.org/${data.nom || 'alexandre_froissart'}`,
                derniere_mise_a_jour: new Date().toISOString().split('T')[0]
            };

            return new Response(JSON.stringify(profile), {
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });

        } catch (error) {
            return new Response(JSON.stringify({
                error: 'Erreur API Root-Me',
                message: error.message
            }), {
                status: 500,
                headers: { ...corsHeaders, 'Content-Type': 'application/json' }
            });
        }
    }
};
