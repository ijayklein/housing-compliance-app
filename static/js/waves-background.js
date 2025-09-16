// Interactive Waves Background Component
class WavesBackground {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            lineColor: options.lineColor || 'rgba(13, 110, 253, 0.3)',
            backgroundColor: options.backgroundColor || 'transparent',
            waveSpeedX: options.waveSpeedX || 0.02,
            waveSpeedY: options.waveSpeedY || 0.01,
            waveAmpX: options.waveAmpX || 40,
            waveAmpY: options.waveAmpY || 20,
            friction: options.friction || 0.9,
            tension: options.tension || 0.01,
            maxCursorMove: options.maxCursorMove || 120,
            xGap: options.xGap || 12,
            yGap: options.yGap || 36,
            interactive: options.interactive !== false,
            particles: options.particles !== false,
            ...options
        };

        this.mouse = { x: 0, y: 0 };
        this.animationId = null;
        this.time = 0;
        
        this.init();
    }

    init() {
        this.createWavesContainer();
        if (this.options.particles) {
            this.createFloatingParticles();
        }
        if (this.options.interactive) {
            this.setupInteractivity();
        }
        this.animate();
    }

    createWavesContainer() {
        // Create main waves background
        const wavesDiv = document.createElement('div');
        wavesDiv.className = 'waves-background';
        if (this.options.interactive) {
            wavesDiv.classList.add('interactive');
        }

        // Create animated wave elements
        const wavesContainer = document.createElement('div');
        wavesContainer.className = 'waves-container';

        for (let i = 0; i < 4; i++) {
            const wave = document.createElement('div');
            wave.className = 'wave';
            wavesContainer.appendChild(wave);
        }

        // Create SVG waves
        const svgWaves = document.createElement('div');
        svgWaves.className = 'svg-waves';
        svgWaves.innerHTML = `
            <svg viewBox="0 0 100 100" preserveAspectRatio="none">
                <path class="wave-path" d="M0,50 Q25,30 50,50 T100,50 L100,100 L0,100 Z"/>
                <path class="wave-path" d="M0,60 Q25,40 50,60 T100,60 L100,100 L0,100 Z"/>
                <path class="wave-path" d="M0,40 Q25,60 50,40 T100,40 L100,100 L0,100 Z"/>
            </svg>
        `;

        wavesDiv.appendChild(wavesContainer);
        wavesDiv.appendChild(svgWaves);
        this.container.appendChild(wavesDiv);

        this.wavesContainer = wavesContainer;
        this.svgWaves = svgWaves;
    }

    createFloatingParticles() {
        const particlesDiv = document.createElement('div');
        particlesDiv.className = 'floating-particles';

        // Create random particles
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random positioning and timing
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 15 + 's';
            particle.style.animationDuration = (12 + Math.random() * 8) + 's';
            
            particlesDiv.appendChild(particle);
        }

        this.container.querySelector('.waves-background').appendChild(particlesDiv);
    }

    setupInteractivity() {
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = ((e.clientY - rect.top) / rect.height) * 2 - 1;
        });

        this.container.addEventListener('mouseleave', () => {
            this.mouse.x = 0;
            this.mouse.y = 0;
        });
    }

    animate() {
        this.time += 0.016; // ~60fps

        if (this.options.interactive && this.wavesContainer) {
            const waves = this.wavesContainer.querySelectorAll('.wave');
            waves.forEach((wave, index) => {
                const factor = (index + 1) * 0.1;
                const moveX = this.mouse.x * this.options.maxCursorMove * factor;
                const moveY = this.mouse.y * this.options.maxCursorMove * factor;
                const rotation = this.time * 20 + index * 90;
                
                wave.style.transform = `translate(${moveX}px, ${moveY}px) rotate(${rotation}deg) scale(${1 + Math.sin(this.time + index) * 0.1})`;
            });
        }

        // Animate SVG wave paths
        if (this.svgWaves) {
            const paths = this.svgWaves.querySelectorAll('.wave-path');
            paths.forEach((path, index) => {
                const offset = index * Math.PI / 3;
                const amplitude = 10 + Math.sin(this.time * this.options.waveSpeedX + offset) * 5;
                const frequency = 0.02 + index * 0.01;
                
                let pathData = 'M0,';
                pathData += (50 + Math.sin(this.time * frequency + offset) * amplitude);
                pathData += ' Q25,';
                pathData += (30 + Math.sin(this.time * frequency + offset + Math.PI/4) * amplitude);
                pathData += ' 50,';
                pathData += (50 + Math.sin(this.time * frequency + offset + Math.PI/2) * amplitude);
                pathData += ' T100,';
                pathData += (50 + Math.sin(this.time * frequency + offset + Math.PI) * amplitude);
                pathData += ' L100,100 L0,100 Z';
                
                path.setAttribute('d', pathData);
            });
        }

        this.animationId = requestAnimationFrame(() => this.animate());
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        const wavesElement = this.container.querySelector('.waves-background');
        if (wavesElement) {
            wavesElement.remove();
        }
    }

    updateTheme(isDark = false) {
        const wavesElement = this.container.querySelector('.waves-background');
        if (wavesElement) {
            if (isDark) {
                wavesElement.classList.add('dark-theme');
            } else {
                wavesElement.classList.remove('dark-theme');
            }
        }
    }
}

// Auto-initialize waves backgrounds
document.addEventListener('DOMContentLoaded', function() {
    // Initialize waves on hero sections and waves-enabled elements
    const heroSections = document.querySelectorAll('.hero-section, .jumbotron, .banner, .waves-enabled');
    heroSections.forEach(section => {
        if (!section.querySelector('.waves-background')) {
            section.style.position = 'relative';
            new WavesBackground(section, {
                interactive: true,
                particles: true,
                waveSpeedX: 0.015,
                waveSpeedY: 0.008
            });
        }
    });

    // Initialize on cards with waves class
    const waveCards = document.querySelectorAll('.card.waves, .waves-card');
    waveCards.forEach(card => {
        if (!card.querySelector('.waves-background')) {
            card.style.position = 'relative';
            card.style.overflow = 'hidden';
            new WavesBackground(card, {
                interactive: false,
                particles: false,
                waveSpeedX: 0.01,
                waveSpeedY: 0.005
            });
        }
    });
});

// Export for manual initialization
window.WavesBackground = WavesBackground;
