/**
 * Module JavaScript pour afficher la progression de l'envoi d'emails Gmail en temps réel
 *
 * Usage:
 *   const tracker = new GmailProgressTracker('job-id-123', {
 *     onUpdate: (data) => console.log('Progression:', data),
 *     onComplete: (data) => console.log('Terminé!', data),
 *     onError: (error) => console.error('Erreur:', error)
 *   });
 *   tracker.start();
 *
 * @author Paulo ALVES
 * @date 2025-01-10
 */

class GmailProgressTracker {
    constructor(jobId, options = {}) {
        this.jobId = jobId;
        this.options = {
            apiUrl: options.apiUrl || `/api/gmail/progress/${jobId}/`,
            updateInterval: options.updateInterval || 1000, // 1 seconde
            onUpdate: options.onUpdate || null,
            onComplete: options.onComplete || null,
            onError: options.onError || null,
            onFailed: options.onFailed || null,
            autoHideOnComplete: options.autoHideOnComplete !== false,
            autoHideDelay: options.autoHideDelay || 3000, // 3 secondes
        };

        this.intervalId = null;
        this.lastStatus = null;
        this.isRunning = false;
    }

    /**
     * Démarre le suivi de la progression
     */
    start() {
        if (this.isRunning) {
            console.warn('Le tracker est déjà en cours d\'exécution');
            return;
        }

        this.isRunning = true;
        this.fetchProgress(); // Fetch immédiatement
        this.intervalId = setInterval(() => this.fetchProgress(), this.options.updateInterval);
    }

    /**
     * Arrête le suivi de la progression
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
    }

    /**
     * Récupère la progression depuis l'API
     */
    async fetchProgress() {
        try {
            const response = await fetch(this.options.apiUrl, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin', // Envoie les cookies de session
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success && result.data) {
                this.handleProgressUpdate(result.data);
            } else {
                throw new Error(result.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('Erreur lors de la récupération de la progression:', error);
            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }

    /**
     * Traite une mise à jour de progression
     */
    handleProgressUpdate(data) {
        const previousStatus = this.lastStatus;
        this.lastStatus = data.status;

        // Appelle le callback onUpdate
        if (this.options.onUpdate) {
            this.options.onUpdate(data);
        }

        // Vérifie si le statut a changé
        if (data.status === 'completed' && previousStatus !== 'completed') {
            this.handleComplete(data);
        } else if (data.status === 'failed' && previousStatus !== 'failed') {
            this.handleFailed(data);
        }

        // Arrête le tracker si le job est terminé ou échoué
        if (data.status === 'completed' || data.status === 'failed') {
            this.stop();
        }
    }

    /**
     * Gère la fin de l'envoi
     */
    handleComplete(data) {
        if (this.options.onComplete) {
            this.options.onComplete(data);
        }
    }

    /**
     * Gère un échec
     */
    handleFailed(data) {
        if (this.options.onFailed) {
            this.options.onFailed(data);
        }
    }

    /**
     * Redémarre le tracker
     */
    restart() {
        this.stop();
        this.lastStatus = null;
        this.start();
    }
}


/**
 * Classe pour afficher visuellement la progression avec une barre de progression
 */
class GmailProgressUI {
    constructor(containerId, jobId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container avec ID "${containerId}" non trouvé`);
        }

        this.jobId = jobId;
        this.options = {
            showDetails: options.showDetails !== false,
            showStats: options.showStats !== false,
            ...options
        };

        this.tracker = null;
        this.elements = {};
        this.init();
    }

    /**
     * Initialise l'interface
     */
    init() {
        this.createUI();
        this.initTracker();
    }

    /**
     * Crée l'interface HTML
     */
    createUI() {
        this.container.innerHTML = `
            <div class="gmail-progress-container" style="
                background: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <!-- Titre -->
                <div class="progress-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                ">
                    <h3 style="margin: 0; font-size: 18px; color: #333;">
                        <span class="progress-icon">📧</span>
                        Envoi des factures
                    </h3>
                    <span class="progress-status-badge" style="
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 12px;
                        font-weight: bold;
                        background: #ffc107;
                        color: #fff;
                    ">En attente...</span>
                </div>

                <!-- Barre de progression -->
                <div class="progress-bar-container" style="
                    background: #f5f5f5;
                    border-radius: 10px;
                    height: 30px;
                    overflow: hidden;
                    margin-bottom: 15px;
                    position: relative;
                ">
                    <div class="progress-bar" style="
                        height: 100%;
                        width: 0%;
                        background: linear-gradient(90deg, #4caf50, #66bb6a);
                        transition: width 0.3s ease;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">
                        <span class="progress-percentage" style="
                            position: absolute;
                            width: 100%;
                            text-align: center;
                            font-weight: bold;
                            color: #333;
                            font-size: 14px;
                        ">0%</span>
                    </div>
                </div>

                <!-- Détails -->
                ${this.options.showDetails ? `
                <div class="progress-details" style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin-bottom: 15px;
                ">
                    <div class="detail-item">
                        <strong>Total:</strong>
                        <span class="detail-total">0</span> emails
                    </div>
                    <div class="detail-item">
                        <strong>Envoyés:</strong>
                        <span class="detail-sent">0</span>
                    </div>
                    <div class="detail-item">
                        <strong>Erreurs:</strong>
                        <span class="detail-failed">0</span>
                    </div>
                    <div class="detail-item">
                        <strong>Vitesse:</strong>
                        <span class="detail-speed">0</span> emails/s
                    </div>
                </div>
                ` : ''}

                <!-- Stats -->
                ${this.options.showStats ? `
                <div class="progress-stats" style="
                    display: flex;
                    justify-content: space-between;
                    font-size: 12px;
                    color: #666;
                ">
                    <span class="stat-current-operation">Préparation...</span>
                    <span class="stat-time-remaining">Calcul...</span>
                </div>
                ` : ''}
            </div>
        `;

        // Référence aux éléments
        this.elements = {
            statusBadge: this.container.querySelector('.progress-status-badge'),
            progressBar: this.container.querySelector('.progress-bar'),
            progressPercentage: this.container.querySelector('.progress-percentage'),
            detailTotal: this.container.querySelector('.detail-total'),
            detailSent: this.container.querySelector('.detail-sent'),
            detailFailed: this.container.querySelector('.detail-failed'),
            detailSpeed: this.container.querySelector('.detail-speed'),
            currentOperation: this.container.querySelector('.stat-current-operation'),
            timeRemaining: this.container.querySelector('.stat-time-remaining'),
        };
    }

    /**
     * Initialise le tracker
     */
    initTracker() {
        this.tracker = new GmailProgressTracker(this.jobId, {
            onUpdate: (data) => this.updateUI(data),
            onComplete: (data) => this.handleComplete(data),
            onFailed: (data) => this.handleFailed(data),
            onError: (error) => this.handleError(error),
        });

        this.tracker.start();
    }

    /**
     * Met à jour l'interface
     */
    updateUI(data) {
        // Statut
        const statusConfig = {
            pending: { text: 'En attente', color: '#ffc107', icon: '⏳' },
            in_progress: { text: 'En cours', color: '#2196f3', icon: '🚀' },
            completed: { text: 'Terminé', color: '#4caf50', icon: '✅' },
            failed: { text: 'Échoué', color: '#f44336', icon: '❌' },
        };

        const status = statusConfig[data.status] || statusConfig.pending;
        this.elements.statusBadge.textContent = status.text;
        this.elements.statusBadge.style.background = status.color;
        this.container.querySelector('.progress-icon').textContent = status.icon;

        // Barre de progression
        const percentage = data.progress_percentage || 0;
        this.elements.progressBar.style.width = `${percentage}%`;
        this.elements.progressPercentage.textContent = `${percentage}%`;

        // Couleur de la barre selon le statut
        if (data.status === 'completed') {
            this.elements.progressBar.style.background = 'linear-gradient(90deg, #4caf50, #66bb6a)';
        } else if (data.status === 'failed') {
            this.elements.progressBar.style.background = 'linear-gradient(90deg, #f44336, #e57373)';
        }

        // Détails
        if (this.options.showDetails) {
            this.elements.detailTotal.textContent = data.total_emails || 0;
            this.elements.detailSent.textContent = data.sent_emails || 0;
            this.elements.detailFailed.textContent = data.failed_emails || 0;
            this.elements.detailSpeed.textContent = (data.emails_per_second || 0).toFixed(1);
        }

        // Stats
        if (this.options.showStats) {
            this.elements.currentOperation.textContent = data.current_operation || 'En cours...';

            if (data.estimated_remaining_time !== null && data.estimated_remaining_time !== undefined) {
                const minutes = Math.floor(data.estimated_remaining_time / 60);
                const seconds = Math.floor(data.estimated_remaining_time % 60);
                this.elements.timeRemaining.textContent =
                    `Temps restant: ${minutes}m ${seconds}s`;
            } else {
                this.elements.timeRemaining.textContent = 'Calcul du temps restant...';
            }
        }
    }

    /**
     * Gère la fin de l'envoi
     */
    handleComplete(data) {
        console.log('Envoi terminé!', data);

        if (this.options.showStats) {
            this.elements.currentOperation.textContent =
                `✅ Terminé! ${data.successful_emails} emails envoyés avec succès`;
            this.elements.timeRemaining.textContent =
                `Durée totale: ${Math.floor(data.duration)}s`;
        }

        // Auto-hide si demandé
        if (this.options.autoHideOnComplete) {
            setTimeout(() => {
                this.container.style.display = 'none';
            }, this.options.autoHideDelay || 3000);
        }
    }

    /**
     * Gère un échec
     */
    handleFailed(data) {
        console.error('Envoi échoué:', data);

        if (this.options.showStats) {
            this.elements.currentOperation.textContent =
                `❌ Erreur: ${data.error_message || 'Erreur inconnue'}`;
            this.elements.timeRemaining.textContent = '';
        }
    }

    /**
     * Gère une erreur
     */
    handleError(error) {
        console.error('Erreur:', error);
        this.elements.statusBadge.textContent = 'Erreur';
        this.elements.statusBadge.style.background = '#f44336';
    }

    /**
     * Détruit l'interface
     */
    destroy() {
        if (this.tracker) {
            this.tracker.stop();
        }
        this.container.innerHTML = '';
    }
}


// Export pour utilisation en module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { GmailProgressTracker, GmailProgressUI };
}