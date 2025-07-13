// Tickr Toys - Particle Effect System
// Creates a swirling multicoloured particle effect for the landing page

class ParticleSystem {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.colors = [
            '#667eea', '#764ba2', '#ffd700', '#ffb347',
            '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
        ];
        this.currencySymbols = ['$', '£', '€', '¥', '₿', '₹', '₽', '₩', '₦', '₪'];
        this.animationId = null;
        this.isRunning = false;
        
        this.init();
    }
    
    init() {
        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        
        this.ctx = this.canvas.getContext('2d');
        
        // Add to particles container
        const container = document.getElementById('particles-container');
        if (container) {
            container.appendChild(this.canvas);
        }
        
        // Set canvas size
        this.resize();
        
        // Create initial particles
        this.createParticles();
        
        // Start animation
        this.start();
        
        // Handle window resize
        window.addEventListener('resize', () => this.resize());
    }
    
    resize() {
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();
        
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        
        this.ctx.scale(dpr, dpr);
        
        this.canvas.style.width = rect.width + 'px';
        this.canvas.style.height = rect.height + 'px';
        
        this.width = rect.width;
        this.height = rect.height;
    }
    
    createParticles() {
        // Adjust particle count based on page type
        const isLandingPage = document.getElementById('particles-container') !== null;
        const baseCount = isLandingPage ? 150 : 80; // Fewer particles on generation page
        const numParticles = Math.min(baseCount, Math.floor((this.width * this.height) / 8000));
        
        for (let i = 0; i < numParticles; i++) {
            this.particles.push(this.createParticle());
        }
    }
    
    createParticle() {
        // Adjust opacity based on page type
        const isLandingPage = document.getElementById('particles-container') !== null;
        const baseOpacity = isLandingPage ? 0.6 : 0.3; // Lower opacity on generation page
        
        return {
            x: Math.random() * this.width,
            y: Math.random() * this.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 3 + 1,
            color: this.colors[Math.floor(Math.random() * this.colors.length)],
            opacity: Math.random() * baseOpacity + 0.1,
            angle: Math.random() * Math.PI * 2,
            angularVelocity: (Math.random() - 0.5) * 0.02,
            swirl: Math.random() * 0.01 + 0.005,
            life: 1.0,
            decay: Math.random() * 0.002 + 0.001,
            symbol: this.currencySymbols[Math.floor(Math.random() * this.currencySymbols.length)],
            fontSize: Math.random() * 8 + 12,
            rotation: Math.random() * Math.PI * 2,
            rotationSpeed: (Math.random() - 0.5) * 0.05
        };
    }
    
    updateParticle(particle) {
        // Apply swirling motion
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        
        const dx = particle.x - centerX;
        const dy = particle.y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Swirl effect
        particle.angle += particle.angularVelocity;
        const swirlForce = particle.swirl * Math.sin(particle.angle);
        
        particle.vx += (-dy / distance) * swirlForce;
        particle.vy += (dx / distance) * swirlForce;
        
        // Add some randomness
        particle.vx += (Math.random() - 0.5) * 0.01;
        particle.vy += (Math.random() - 0.5) * 0.01;
        
        // Apply velocity damping
        particle.vx *= 0.99;
        particle.vy *= 0.99;
        
        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;
        
        // Update life
        particle.life -= particle.decay;
        
        // Update rotation
        particle.rotation += particle.rotationSpeed;
        
        // Wrap around edges
        if (particle.x < 0) particle.x = this.width;
        if (particle.x > this.width) particle.x = 0;
        if (particle.y < 0) particle.y = this.height;
        if (particle.y > this.height) particle.y = 0;
        
        // Reset particle if life is over
        if (particle.life <= 0) {
            Object.assign(particle, this.createParticle());
        }
    }
    
    drawParticle(particle) {
        this.ctx.save();
        
        // Set opacity based on life
        const alpha = particle.opacity * particle.life;
        this.ctx.globalAlpha = alpha;
        
        // Apply rotation and translation
        this.ctx.translate(particle.x, particle.y);
        this.ctx.rotate(particle.rotation);
        
        // Set font and color
        this.ctx.font = `${particle.fontSize}px Arial`;
        this.ctx.fillStyle = particle.color;
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        
        // Add glow effect
        this.ctx.shadowColor = particle.color;
        this.ctx.shadowBlur = 10;
        this.ctx.shadowOffsetX = 0;
        this.ctx.shadowOffsetY = 0;
        
        // Draw currency symbol
        this.ctx.fillText(particle.symbol, 0, 0);
        
        // Draw a slightly smaller version on top for better visibility
        this.ctx.shadowBlur = 0;
        this.ctx.globalAlpha = alpha * 0.6;
        this.ctx.fillStyle = '#cccccc';
        this.ctx.fillText(particle.symbol, 0, 0);
        
        this.ctx.restore();
    }
    
    drawConnections() {
        this.ctx.save();
        
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const p1 = this.particles[i];
                const p2 = this.particles[j];
                
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    const alpha = (1 - distance / 100) * 0.1 * p1.life * p2.life;
                    
                    this.ctx.globalAlpha = alpha;
                    this.ctx.strokeStyle = '#ffffff';
                    this.ctx.lineWidth = 0.5;
                    
                    this.ctx.beginPath();
                    this.ctx.moveTo(p1.x, p1.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            }
        }
        
        this.ctx.restore();
    }
    
    animate() {
        if (!this.isRunning) return;
        
        // Clear canvas
        this.ctx.clearRect(0, 0, this.width, this.height);
        
        // Update and draw particles
        for (const particle of this.particles) {
            this.updateParticle(particle);
            this.drawParticle(particle);
        }
        
        // Draw connections between nearby particles
        this.drawConnections();
        
        // Continue animation
        this.animationId = requestAnimationFrame(() => this.animate());
    }
    
    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            this.animate();
        }
    }
    
    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
    
    destroy() {
        this.stop();
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        window.removeEventListener('resize', this.resize);
    }
}

// Initialize particle system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize on both landing page and generation page
    if (document.getElementById('particles-container') || document.body) {
        // Create particles container if it doesn't exist (for generation page)
        if (!document.getElementById('particles-container')) {
            const container = document.createElement('div');
            container.id = 'particles-container';
            container.style.position = 'fixed';
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100%';
            container.style.height = '100%';
            container.style.zIndex = '0';
            container.style.pointerEvents = 'none';
            document.body.insertBefore(container, document.body.firstChild);
        }
        
        const particleSystem = new ParticleSystem();
        
        // Optional: Pause particles when page is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                particleSystem.stop();
            } else {
                particleSystem.start();
            }
        });
    }
});

// Function for landing page CTA button
function startExperience() {
    window.location.href = '/generate';
}