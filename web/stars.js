// Animated Stars Effect
// Bu dosyayı body'nin sonunda çağırın: <script src="stars.js"></script>

(function() {
    // Stars container oluştur
    var starsContainer = document.createElement('div');
    starsContainer.id = 'starsBackground';
    starsContainer.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0;';
    document.body.insertBefore(starsContainer, document.body.firstChild);

    // Keyframe animation ekle
    var style = document.createElement('style');
    style.textContent = `
        @keyframes starFloat {
            0% {
                transform: translateY(100vh);
                opacity: 0;
            }
            10% {
                opacity: 0.8;
            }
            90% {
                opacity: 0.8;
            }
            100% {
                transform: translateY(-100px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // 100 yıldız oluştur
    for (var i = 0; i < 100; i++) {
        var star = document.createElement('div');
        star.style.position = 'absolute';
        star.style.width = (Math.random() * 3 + 1) + 'px';
        star.style.height = star.style.width;
        star.style.background = '#FFCC00';
        star.style.borderRadius = '50%';
        star.style.left = Math.random() * 100 + '%';
        star.style.animation = 'starFloat ' + (Math.random() * 20 + 10) + 's linear infinite';
        star.style.animationDelay = Math.random() * 10 + 's';
        starsContainer.appendChild(star);
    }

    // Main content'e z-index ver
    var containers = document.querySelectorAll('.container, .selection-container, .mapping-container, .upload-container');
    for (var j = 0; j < containers.length; j++) {
        containers[j].style.position = 'relative';
        containers[j].style.zIndex = '1';
    }
})();

