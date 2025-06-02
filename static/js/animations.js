// Tajweed-specific animations
const tajweedAnimations = {
    // Animate when a word is highlighted
    highlightWord: (word) => {
        gsap.to(word, {
            duration: 0.3,
            scale: 1.05,
            backgroundColor: 'var(--highlight-bg)',
            ease: 'power2.out',
            yoyo: true,
            repeat: 1
        });
    },

    // Animate feedback messages
    showFeedback: (element) => {
        gsap.from(element, {
            duration: 0.5,
            opacity: 0,
            y: 20,
            ease: 'back.out(1.7)',
            onComplete: () => {
                gsap.to(element, {
                    duration: 0.3,
                    scale: 1.02,
                    yoyo: true,
                    repeat: 1
                });
            }
        });
    },

    // Animate recording state
    recordingPulse: (element) => {
        gsap.to(element, {
            duration: 1,
            scale: 1.02,
            backgroundColor: 'var(--error-color)',
            ease: 'power1.inOut',
            yoyo: true,
            repeat: -1
        });
    },

    // Animate success state
    successAnimation: (element) => {
        gsap.timeline()
            .to(element, {
                duration: 0.3,
                scale: 1.1,
                backgroundColor: 'var(--success-start)',
                ease: 'power2.out'
            })
            .to(element, {
                duration: 0.2,
                scale: 1,
                backgroundColor: 'var(--success-end)',
                ease: 'power2.in'
            });
    },

    // Animate error state
    errorAnimation: (element) => {
        gsap.timeline()
            .to(element, {
                duration: 0.1,
                x: -10,
                ease: 'power1.inOut'
            })
            .to(element, {
                duration: 0.1,
                x: 10,
                ease: 'power1.inOut'
            })
            .to(element, {
                duration: 0.1,
                x: -5,
                ease: 'power1.inOut'
            })
            .to(element, {
                duration: 0.1,
                x: 0,
                ease: 'power1.inOut'
            });
    },

    // Animate loading state
    loadingAnimation: (element) => {
        gsap.to(element, {
            duration: 1,
            opacity: 0.5,
            scale: 0.98,
            ease: 'power1.inOut',
            yoyo: true,
            repeat: -1
        });
    },

    // Animate navigation menu
    toggleMenu: (menu, isOpen) => {
        gsap.to(menu, {
            duration: 0.3,
            height: isOpen ? 'auto' : 0,
            opacity: isOpen ? 1 : 0,
            ease: 'power2.inOut'
        });
    },

    // Animate theme switch
    themeSwitch: (element) => {
        gsap.to(element, {
            duration: 0.5,
            rotation: 360,
            scale: 1.2,
            ease: 'back.out(1.7)',
            yoyo: true,
            repeat: 1
        });
    }
};

// Export the animations
window.tajweedAnimations = tajweedAnimations; 