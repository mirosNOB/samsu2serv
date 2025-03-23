document.addEventListener('DOMContentLoaded', function() {
    // Автоматическое закрытие сообщений об успехе через 5 секунд
    const alerts = document.querySelectorAll('.alert-success, .alert-info');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Превью изображения перед загрузкой
    const imageInputs = document.querySelectorAll('input[type="file"][accept="image/*"]');
    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            if (this.files && this.files[0]) {
                const previewId = `${this.id}-preview`;
                let preview = document.getElementById(previewId);
                
                if (!preview) {
                    preview = document.createElement('img');
                    preview.id = previewId;
                    preview.className = 'img-fluid rounded mt-2';
                    preview.style.maxHeight = '200px';
                    this.parentNode.appendChild(preview);
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Обработка превью цвета никнейма
    const colorPicker = document.getElementById('nickname_color');
    if (colorPicker) {
        const username = document.querySelector('h3');
        colorPicker.addEventListener('input', function() {
            username.style.color = this.value;
        });
    }

    // Индикатор оставшихся символов в статусе
    const statusInput = document.getElementById('status');
    if (statusInput) {
        const maxLength = statusInput.getAttribute('maxlength');
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'form-text';
        statusInput.parentNode.appendChild(feedbackDiv);
        
        function updateCounter() {
            const remaining = maxLength - statusInput.value.length;
            feedbackDiv.textContent = `Осталось символов: ${remaining}`;
        }
        
        statusInput.addEventListener('input', updateCounter);
        updateCounter(); // Инициализация при загрузке
    }
    
    // Отключаем анимацию карточек на мобильных устройствах
    if ('ontouchstart' in window) {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.style.transition = 'none';
        });
    } else {
        // Анимация при наведении на карточки (только для десктопа)
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px)';
                this.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
    }
    
    // Улучшение работы навигации на мобильных устройствах
    if (window.innerWidth < 768) {
        const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                const navbarCollapse = document.querySelector('.navbar-collapse');
                if (navbarCollapse.classList.contains('show')) {
                    const bsNavbar = bootstrap.Collapse.getInstance(navbarCollapse);
                    if (bsNavbar) {
                        bsNavbar.hide();
                    }
                }
            });
        });

        // Улучшаем отображение комментариев на мобильных устройствах
        const comments = document.querySelectorAll('.comment');
        comments.forEach(comment => {
            comment.classList.add('py-2');
        });
    }
    
    // Обнаружение ориентации устройства и адаптация интерфейса
    function handleOrientationChange() {
        if (window.innerHeight > window.innerWidth) {
            document.body.classList.add('portrait');
            document.body.classList.remove('landscape');
        } else {
            document.body.classList.add('landscape');
            document.body.classList.remove('portrait');
        }
    }
    
    // Инициализируем ориентацию и добавляем слушатель
    handleOrientationChange();
    window.addEventListener('resize', handleOrientationChange);
    
    // Добавляем "pull to refresh" эффект
    let touchStartY = 0;
    const mainContent = document.querySelector('.main-content');
    
    if (mainContent && 'ontouchstart' in window) {
        document.addEventListener('touchstart', function(e) {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchmove', function(e) {
            const touchY = e.touches[0].clientY;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            // Если мы в верху страницы и тянем вниз
            if (scrollTop === 0 && touchY > touchStartY + 50) {
                e.preventDefault();
                mainContent.style.transform = `translateY(${Math.min(touchY - touchStartY, 100)}px)`;
                mainContent.style.transition = 'none';
            }
        }, { passive: false });
        
        document.addEventListener('touchend', function() {
            if (mainContent.style.transform !== '') {
                mainContent.style.transform = '';
                mainContent.style.transition = 'transform 0.3s ease-out';
                if (mainContent.style.transform.includes('translateY(100px)')) {
                    location.reload();
                }
            }
        }, { passive: true });
    }
}); 