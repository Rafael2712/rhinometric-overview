const { createApp } = Vue;

createApp({
    data() {
        return {
            apis: [],
            loading: false,
            showForm: false,
            newApi: {
                name: '',
                endpoint: '',
                authType: 'none',
                authToken: '',
                interval: 60,
                enabled: true
            },
            testResult: null,
            notification: null,
            apiProxyUrl: 'http://localhost:8090',
            licenseServerUrl: 'http://localhost:5000'
        }
    },
    mounted() {
        this.refreshApis();
        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (!this.showForm) {
                this.refreshApis();
            }
        }, 30000);
    },
    methods: {
        async refreshApis() {
            this.loading = true;
            try {
                // Try License Server first (has external_apis endpoint)
                const response = await fetch(`${this.licenseServerUrl}/api/external-apis`);
                if (response.ok) {
                    this.apis = await response.json();
                    await this.fetchHealthStatus();
                } else {
                    // Fallback: use demo data
                    this.apis = this.getDemoApis();
                }
            } catch (error) {
                console.error('Error fetching APIs:', error);
                // Use demo data on error
                this.apis = this.getDemoApis();
            } finally {
                this.loading = false;
            }
        },

        getDemoApis() {
            return [
                {
                    id: 1,
                    name: 'coindesk_btc',
                    endpoint: 'https://api.coindesk.com/v1/bpi/currentprice.json',
                    auth_type: 'none',
                    scrape_interval: 60,
                    status: 'healthy',
                    total_requests: 42,
                    last_success: new Date().toISOString()
                },
                {
                    id: 2,
                    name: 'github_status',
                    endpoint: 'https://www.githubstatus.com/api/v2/status.json',
                    auth_type: 'none',
                    scrape_interval: 300,
                    status: 'healthy',
                    total_requests: 15,
                    last_success: new Date().toISOString()
                },
                {
                    id: 3,
                    name: 'openmeteo_weather',
                    endpoint: 'https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true',
                    auth_type: 'none',
                    scrape_interval: 600,
                    status: 'healthy',
                    total_requests: 8,
                    last_success: new Date().toISOString()
                }
            ];
        },

        async fetchHealthStatus() {
            try {
                const response = await fetch(`${this.apiProxyUrl}/api/health/all`);
                if (response.ok) {
                    const healthData = await response.json();
                    // Update API statuses
                    this.apis.forEach(api => {
                        if (healthData[api.name]) {
                            api.status = healthData[api.name].status;
                        }
                    });
                }
            } catch (error) {
                console.error('Error fetching health status:', error);
            }
        },

        async addApi() {
            try {
                const apiData = {
                    name: this.newApi.name,
                    endpoint: this.newApi.endpoint,
                    auth_type: this.newApi.authType,
                    auth_token: this.newApi.authToken || null,
                    scrape_interval: this.newApi.interval,
                    is_active: this.newApi.enabled
                };

                // Try to add via License Server
                const response = await fetch(`${this.licenseServerUrl}/api/external-apis`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(apiData)
                });

                if (response.ok) {
                    const result = await response.json();
                    this.showNotification('API agregada exitosamente', 'success');
                    this.showForm = false;
                    this.resetForm();
                    await this.refreshApis();
                } else {
                    // Fallback: register via API Proxy
                    const proxyResponse = await fetch(`${this.apiProxyUrl}/api/register`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(apiData)
                    });

                    if (proxyResponse.ok) {
                        this.showNotification('API registrada en proxy exitosamente', 'success');
                        this.showForm = false;
                        this.resetForm();
                        await this.refreshApis();
                    } else {
                        throw new Error('No se pudo agregar la API');
                    }
                }
            } catch (error) {
                console.error('Error adding API:', error);
                this.showNotification('Error al agregar API: ' + error.message, 'error');
            }
        },

        async testConnection() {
            this.testResult = null;
            try {
                const response = await fetch(this.newApi.endpoint, {
                    method: 'GET',
                    headers: this.getAuthHeaders(this.newApi.authType, this.newApi.authToken)
                });

                if (response.ok) {
                    const data = await response.text();
                    this.testResult = {
                        success: true,
                        message: '✓ Conexión exitosa!',
                        details: data.substring(0, 200) + (data.length > 200 ? '...' : '')
                    };
                } else {
                    this.testResult = {
                        success: false,
                        message: `✗ Error: ${response.status} ${response.statusText}`,
                        details: null
                    };
                }
            } catch (error) {
                this.testResult = {
                    success: false,
                    message: '✗ Error de conexión',
                    details: error.message
                };
            }
        },

        async testApiConnection(api) {
            try {
                const response = await fetch(api.endpoint);
                if (response.ok) {
                    this.showNotification(`✓ ${api.name} está funcionando correctamente`, 'success');
                } else {
                    this.showNotification(`✗ ${api.name} respondió con error ${response.status}`, 'error');
                }
            } catch (error) {
                this.showNotification(`✗ ${api.name} no responde: ${error.message}`, 'error');
            }
        },

        async deleteApi(api) {
            if (!confirm(`¿Eliminar API "${api.name}"?`)) return;

            try {
                const response = await fetch(`${this.licenseServerUrl}/api/external-apis/${api.id}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    this.showNotification('API eliminada exitosamente', 'success');
                    await this.refreshApis();
                } else {
                    // Fallback: remove from local list
                    this.apis = this.apis.filter(a => a.id !== api.id);
                    this.showNotification('API eliminada de la lista local', 'info');
                }
            } catch (error) {
                console.error('Error deleting API:', error);
                this.showNotification('Error al eliminar API: ' + error.message, 'error');
            }
        },

        getAuthHeaders(authType, authToken) {
            const headers = {};
            if (authType === 'bearer' && authToken) {
                headers['Authorization'] = `Bearer ${authToken}`;
            } else if (authType === 'api_key' && authToken) {
                headers['X-API-Key'] = authToken;
            }
            return headers;
        },

        resetForm() {
            this.newApi = {
                name: '',
                endpoint: '',
                authType: 'none',
                authToken: '',
                interval: 60,
                enabled: true
            };
            this.testResult = null;
        },

        formatDate(isoString) {
            if (!isoString) return 'N/A';
            const date = new Date(isoString);
            return date.toLocaleString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        showNotification(message, type = 'info') {
            this.notification = { message, type };
            setTimeout(() => {
                this.notification = null;
            }, 5000);
        }
    }
}).mount('#app');
