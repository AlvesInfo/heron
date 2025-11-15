/**
 * Module JavaScript générique pour SSE (Server-Sent Events)
 * RÉUTILISABLE pour toutes les jauges de progression de l'application
 *
 * Usage:
 *   const ui = new SSEProgressUI('container-id', 'job-123', {
 *     title: 'Mon processus',
 *     onComplete: () => alert('Fini!')
 *   });
 *
 * @author Paulo ALVES (via Claude Code)
 * @date 2025-01-10
 */

/**
 * Classe de base pour écouter les événements SSE
 * Peut être utilisée seule ou avec SSEProgressUI
 */
class SSEProgressListener {
    constructor(channelName, options = {}) {
        this.channelName = channelName;
        this.options = {
            onStart: options.onStart || null,
            onProgress: options.onProgress || null,
            onComplete: options.onComplete || null,
            onError: options.onError || null,
            onWarning: options.onWarning || null,
            onCustom: options.onCustom || null,
            reconnect: options.reconnect !== false,
            debug: options.debug || false,
        };

        this.eventSource = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    /**
     * Démarre l'écoute des événements SSE
     */
    start() {
        const url = `/events/?channel=progress-${this.channelName}`;

        if (this.options.debug) {
            console.log(`[SSE] Connexion à ${url}`);
        }

        this.eventSource = new EventSource(url);

        // Connexion établie
        this.eventSource.onopen = () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            if (this.options.debug) {
                console.log('[SSE] ✅ Connecté');
            }
        };

        // Événement : début
        this.eventSource.addEventListener('start', (event) => {
            const data = JSON.parse(event.data);
            if (this.options.debug) {
                console.log('[SSE] 🚀 Start:', data);
            }
            if (this.options.onStart) {
                this.options.onStart(data);
            }
        });

        // Événement : progression
        this.eventSource.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            if (this.options.debug) {
                console.log(`[SSE] 📊 Progress: ${data.percentage}%`, data);
            }
            if (this.options.onProgress) {
                this.options.onProgress(data);
            }
        });

        // Événement : terminé
        this.eventSource.addEventListener('complete', (event) => {
            const data = JSON.parse(event.data);
            if (this.options.debug) {
                console.log('[SSE] ✅ Complete:', data);
            }
            if (this.options.onComplete) {
                this.options.onComplete(data);
            }
            this.stop();
        });

        // Événement : erreur (du processus, pas de connexion)
        this.eventSource.addEventListener('error', (event) => {
            const data = JSON.parse(event.data);
            if (this.options.debug) {
                console.error('[SSE] ❌ Error:', data);
            }
            if (this.options.onError) {
                this.options.onError(data);
            }
        });

        // Événement : avertissement
        this.eventSource.addEventListener('warning', (event) => {
            const data = JSON.parse(event.data);
            if (this.options.debug) {
                console.warn('[SSE] ⚠️  Warning:', data);
            }
            if (this.options.onWarning) {
                this.options.onWarning(data);
            }
        });

        // Événement custom
        if (this.options.onCustom) {
            this.eventSource.addEventListener('message', (event) => {
                const data = JSON.parse(event.data);
                this.options.onCustom(event.type, data);
            });
        }

        // Erreur de connexion SSE
        this.eventSource.onerror = (error) => {
            if (this.options.debug) {
                console.error('[SSE] ❌ Connection error:', error);
            }
            this.isConnected = false;

            if (this.options.reconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * this.reconnectAttempts, 5000);
                if (this.options.debug) {
                    console.log(`[SSE] Reconnexion dans ${delay}ms (tentative ${this.reconnectAttempts})`);
                }
                setTimeout(() => this.start(), delay);
            } else {
                this.stop();
            }
        };
    }

    /**
     * Arrête l'écoute
     */
    stop() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.isConnected = false;
            if (this.options.debug) {
                console.log('[SSE] 🔌 Déconnecté');
            }
        }
    }

    /**
     * Vérifie si connecté
     */
    isActive() {
        return this.isConnected;
    }
}


/**
 * Composant UI complet avec jauge de progression SSE
 * Utilise SSEProgressListener en interne
 */
class SSEProgressUI {
    constructor(containerId, channelName, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            throw new Error(`Container ${containerId} introuvable`);
        }

        this.options = {
            title: options.title || 'Progression',
            icon: options.icon || '⏳',
            showDetails: options.showDetails !== false,
            showStats: options.showStats !== false,
            autoHideOnComplete: options.autoHideOnComplete || false,
            autoHideDelay: options.autoHideDelay || 3000,
            debug: options.debug || false,
            // Callbacks personnalisés
            onStart: options.onStart || null,
            onProgress: options.onProgress || null,
            onComplete: options.onComplete || null,
            onError: options.onError || null,
        };

        this.listener = new SSEProgressListener(channelName, {
            onStart: (data) => this.handleStart(data),
            onProgress: (data) => this.handleProgress(data),
            onComplete: (data) => this.handleComplete(data),
            onError: (data) => this.handleError(data),
            onWarning: (data) => this.handleWarning(data),
            debug: this.options.debug,
        });

        this.createUI();
        this.listener.start();
    }

    createUI() {
        this.container.innerHTML = `
            <div class="sse-progress-container" style="
                background: #fff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div class="progress-header" style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                ">
                    <h3 style="margin: 0; font-size: 18px; color: #333;">
                        <span class="progress-icon">${this.options.icon}</span>
                        ${this.options.title}
                    </h3>
                    <span class="progress-status" style="
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-size: 12px;
                        font-weight: bold;
                        background: #ffc107;
                        color: #fff;
                    ">Connexion...</span>
                </div>

                <div class="progress-bar-container" style="
                    background: #f5f5f5;
                    border-radius: 10px;
                    height: 30px;
                    overflow: hidden;
                    position: relative;
                    margin-bottom: 15px;
                ">
                    <div class="progress-bar" style="
                        height: 100%;
                        width: 0%;
                        background: linear-gradient(90deg, #4caf50, #66bb6a);
                        transition: width 0.3s ease;
                    "></div>
                    <span class="progress-percentage" style="
                        position: absolute;
                        width: 100%;
                        text-align: center;
                        line-height: 30px;
                        font-weight: bold;
                        color: #333;
                    ">0%</span>
                </div>

                ${this.options.showDetails ? `
                <div class="progress-details" style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 10px;
                    margin-bottom: 15px;
                    font-size: 14px;
                ">
                    <div><strong>Total:</strong> <span class="detail-total">-</span></div>
                    <div><strong>Traités:</strong> <span class="detail-current">-</span></div>
                    <div><strong>Restants:</strong> <span class="detail-remaining">-</span></div>
                </div>
                ` : ''}

                ${this.options.showStats ? `
                <div class="progress-stats" style="
                    font-size: 12px;
                    color: #666;
                    min-height: 20px;
                ">
                    <div class="stat-message">Connexion au serveur...</div>
                </div>
                ` : ''}
            </div>
        `;

        this.elements = {
            icon: this.container.querySelector('.progress-icon'),
            status: this.container.querySelector('.progress-status'),
            bar: this.container.querySelector('.progress-bar'),
            percentage: this.container.querySelector('.progress-percentage'),
            total: this.container.querySelector('.detail-total'),
            current: this.container.querySelector('.detail-current'),
            remaining: this.container.querySelector('.detail-remaining'),
            message: this.container.querySelector('.stat-message'),
        };
    }

    handleStart(data) {
        this.elements.icon.textContent = '🚀';
        this.elements.status.textContent = 'En cours';
        this.elements.status.style.background = '#2196f3';

        if (this.elements.total) this.elements.total.textContent = data.total;
        if (this.elements.current) this.elements.current.textContent = '0';
        if (this.elements.remaining) this.elements.remaining.textContent = data.total;
        if (this.elements.message) {
            this.elements.message.textContent = data.message || 'Démarrage...';
        }

        if (this.options.onStart) {
            this.options.onStart(data);
        }
    }

    handleProgress(data) {
        const percentage = data.percentage || 0;
        this.elements.bar.style.width = `${percentage}%`;
        this.elements.percentage.textContent = `${percentage}%`;

        if (this.elements.current) this.elements.current.textContent = data.current;
        if (this.elements.total) this.elements.total.textContent = data.total;
        if (this.elements.remaining) this.elements.remaining.textContent = data.remaining;
        if (this.elements.message && data.message) {
            this.elements.message.textContent = data.message;
        }

        if (this.options.onProgress) {
            this.options.onProgress(data);
        }
    }

    handleComplete(data) {
        this.elements.icon.textContent = '✅';
        this.elements.status.textContent = 'Terminé';
        this.elements.status.style.background = '#4caf50';
        this.elements.bar.style.width = '100%';
        this.elements.percentage.textContent = '100%';

        if (this.elements.message) {
            this.elements.message.textContent = data.message || 'Terminé avec succès!';
        }

        if (this.options.onComplete) {
            this.options.onComplete(data);
        }

        if (this.options.autoHideOnComplete) {
            setTimeout(() => {
                this.container.style.display = 'none';
            }, this.options.autoHideDelay);
        }
    }

    handleError(data) {
        this.elements.icon.textContent = '❌';
        this.elements.status.textContent = 'Erreur';
        this.elements.status.style.background = '#f44336';
        this.elements.bar.style.background = 'linear-gradient(90deg, #f44336, #e57373)';

        if (this.elements.message) {
            this.elements.message.textContent = data.error || 'Une erreur est survenue';
        }

        if (this.options.onError) {
            this.options.onError(data);
        }
    }

    handleWarning(data) {
        if (this.elements.message) {
            this.elements.message.textContent = '⚠️ ' + (data.warning || data.message || 'Avertissement');
        }
    }

    destroy() {
        this.listener.stop();
        this.container.innerHTML = '';
    }
}

// Export pour utilisation en module
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SSEProgressListener, SSEProgressUI };
}