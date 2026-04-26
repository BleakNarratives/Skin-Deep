import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

def simulate_ink_dispersion(needle_vibration_freq, skin_density):
    """
    Particle simulation of ink entering skin
    """
    fig, ax = plt.subplots()
    
    # Initialize particles
    n_particles = 500
    particles = np.zeros((n_particles, 4))  # x, y, vx, vy
    
    # Start at needle tip
    particles[:, 0] = 0.5  # center x
    particles[:, 1] = 1.0  # start y (at skin surface)
    
    # Random velocities based on needle vibration
    particles[:, 2] = np.random.normal(0, 0.01 * needle_vibration_freq, n_particles)
    particles[:, 3] = np.random.normal(-0.02, 0.005, n_particles)
    
    scat = ax.scatter(particles[:, 0], particles[:, 1], s=1, c='black')
    
    # Skin boundaries
    ax.axhline(y=0.8, color='brown', linestyle='--', alpha=0.5, label='Epidermis')
    ax.axhline(y=0.6, color='pink', linestyle='--', alpha=0.5, label='Dermis')
    ax.axhline(y=0.4, color='red', linestyle='--', alpha=0.3, label='Capillaries')
    
    def update(frame):
        # Update particle positions
        particles[:, 0] += particles[:, 2]
        particles[:, 1] += particles[:, 3]
        
        # Bounce off skin "fibers"
        mask = particles[:, 1] < 0.4  # Hit capillary layer
        particles[mask, 3] = -particles[mask, 3] * 0.3  # Dampened bounce
        
        # Random walk (Brownian motion in tissue)
        particles[:, 0] += np.random.normal(0, 0.001, n_particles)
        particles[:, 1] += np.random.normal(0, 0.0005, n_particles)
        
        scat.set_offsets(particles[:, :2])
        return scat,
    
    ani = FuncAnimation(fig, update, frames=200, interval=50, blit=True)
    plt.title("Ink Dispersion in Skin Tissue")
    plt.xlabel("Lateral Spread")
    plt.ylabel("Depth")
    plt.legend()
    plt.show()