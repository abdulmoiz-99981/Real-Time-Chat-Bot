// JavaScript SDK
class AIChat {
    constructor(apiUrl, apiKey) {
        this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
        this.apiKey = apiKey;
        this.defaultModel = 'gpt-3.5-turbo';
    }

    async listModels() {
        const response = await this._makeRequest('GET', '/v1/models');
        return response.data;
    }

    async chat(messages, options = {}) {
        const payload = {
            model: options.model || this.defaultModel,
            messages: messages,
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || null,
            top_p: options.topP || 1.0,
            stream: options.stream || false,
            stop: options.stop || null,
            presence_penalty: options.presencePenalty || 0.0,
            frequency_penalty: options.frequencyPenalty || 0.0,
            user: options.user || null
        };

        if (options.stream) {
            return this._streamChat(payload);
        } else {
            const response = await this._makeRequest('POST', '/v1/chat/completions', payload);
            return response;
        }
    }

    async _streamChat(payload) {
        const response = await fetch(`${this.apiUrl}/v1/chat/completions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        return {
            async *[Symbol.asyncIterator]() {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split('\n');

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') return;
                            
                            try {
                                yield JSON.parse(data);
                            } catch (e) {
                                console.error('Error parsing streaming data:', e);
                            }
                        }
                    }
                }
            }
        };
    }

    async _makeRequest(method, endpoint, data = null) {
        const url = `${this.apiUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.apiKey}`
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    // Utility methods
    createMessage(role, content) {
        return { role, content };
    }

    async simpleChat(userMessage, options = {}) {
        const messages = [this.createMessage('user', userMessage)];
        const response = await this.chat(messages, options);
        return response.choices[0].message.content;
    }

    async healthCheck() {
        try {
            const response = await this._makeRequest('GET', '/health');
            return response.status === 'healthy';
        } catch {
            return false;
        }
    }
}

// Usage Examples
async function examples() {
    const client = new AIChat('http://localhost:8000', 'sk-test123');

    // 1. Simple chat
    try {
        const response = await client.simpleChat('Hello, how are you?');
        console.log('Response:', response);
    } catch (error) {
        console.error('Error:', error.message);
    }

    // 2. Full conversation
    const messages = [
        client.createMessage('system', 'You are a helpful assistant.'),
        client.createMessage('user', 'What is the capital of France?')
    ];

    try {
        const response = await client.chat(messages, {
            model: 'gpt-3.5-turbo',
            temperature: 0.7,
            maxTokens: 150
        });
        console.log('Assistant:', response.choices[0].message.content);
    } catch (error) {
        console
