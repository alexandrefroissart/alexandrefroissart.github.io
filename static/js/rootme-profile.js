/**
 * Root-Me Profile Widget - JavaScript Client
 * 
 * Ce script récupère les données Root-Me via le Cloudflare Worker
 * et met à jour l'affichage en temps réel.
 */

(function () {
    // Configuration - À MODIFIER avec l'URL de ton worker Cloudflare
    const WORKER_URL = 'https://rootme-proxy.YOUR-SUBDOMAIN.workers.dev';
    const ROOTME_UID = '1071705';
    const ROOTME_PROFILE_URL = 'https://www.root-me.org/alexandre_froissart';

    // Sélecteurs DOM
    const container = document.getElementById('rootme-profile');
    if (!container) return;

    // Afficher le spinner de chargement
    function showLoading() {
        container.innerHTML = `
            <div class="rootme-card rootme-loading">
                <div class="rootme-spinner"></div>
                <p>Chargement du profil Root-Me...</p>
            </div>
        `;
    }

    // Afficher les données du profil
    function showProfile(data) {
        container.innerHTML = `
            <div class="rootme-card">
                <div class="rootme-header">
                    <span class="rootme-verified" title="Données récupérées en temps réel via l'API Root-Me">
                        ✓ Vérifié en direct
                    </span>
                </div>
                <div class="rootme-stats">
                    <div class="rootme-stat">
                        <span class="rootme-value">${data.score}</span>
                        <span class="rootme-label">Points</span>
                    </div>
                    <div class="rootme-stat">
                        <span class="rootme-value">#${data.position}</span>
                        <span class="rootme-label">Classement</span>
                    </div>
                    <div class="rootme-stat">
                        <span class="rootme-value">${data.challenges_resolus}</span>
                        <span class="rootme-label">Challenges</span>
                    </div>
                </div>
                <a href="${data.profil_url}" target="_blank" rel="noopener" class="rootme-link">
                    Voir le profil officiel →
                </a>
                <p class="rootme-update">Mis à jour: ${data.derniere_mise_a_jour}</p>
            </div>
        `;
    }

    // Afficher une erreur
    function showError() {
        container.innerHTML = `
            <div class="rootme-card rootme-error">
                <p>Impossible de charger le profil Root-Me</p>
                <a href="${ROOTME_PROFILE_URL}" target="_blank" rel="noopener" class="rootme-link">
                    Voir le profil sur Root-Me →
                </a>
            </div>
        `;
    }

    // Récupérer les données
    async function fetchProfile() {
        showLoading();

        try {
            const response = await fetch(`${WORKER_URL}/auteurs/${ROOTME_UID}`);

            if (!response.ok) {
                throw new Error('API error');
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            showProfile(data);
        } catch (error) {
            console.error('Root-Me API error:', error);
            showError();
        }
    }

    // Lancer la récupération au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fetchProfile);
    } else {
        fetchProfile();
    }
})();
