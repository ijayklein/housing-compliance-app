// Main JavaScript for Housing Compliance System

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced navbar scroll effect
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        // Hide navbar on scroll down, show on scroll up
        if (scrollTop > lastScrollTop && scrollTop > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScrollTop = scrollTop;
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add fade-in animation to cards
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    }, observerOptions);

    // Observe all cards
    document.querySelectorAll('.card').forEach(card => {
        observer.observe(card);
    });

    // Form validation helpers
    window.validateForm = function(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;

        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });

        return isValid;
    };

    // Number formatting helper
    window.formatNumber = function(num) {
        return new Intl.NumberFormat('en-US').format(num);
    };

    // Show loading state
    window.showLoading = function(elementId, message = 'Loading...') {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">${message}</p>
                </div>
            `;
        }
    };

    // Show success message
    window.showSuccess = function(message, duration = 5000) {
        showToast(message, 'success', duration);
    };

    // Show error message
    window.showError = function(message, duration = 5000) {
        showToast(message, 'danger', duration);
    };

    // Show warning message
    window.showWarning = function(message, duration = 5000) {
        showToast(message, 'warning', duration);
    };

    // Show info message
    window.showInfo = function(message, duration = 5000) {
        showToast(message, 'info', duration);
    };

    // Toast notification system
    function showToast(message, type = 'info', duration = 5000) {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1055';
            document.body.appendChild(toastContainer);
        }

        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">
                        <i class="fas fa-${getIconForType(type)} me-2"></i>
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Initialize and show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });
        
        toast.show();

        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    }

    function getIconForType(type) {
        switch(type) {
            case 'success': return 'check-circle';
            case 'danger': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            case 'info': return 'info-circle';
            default: return 'info-circle';
        }
    }

    // API helper functions
    window.apiCall = async function(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    };

    // Local storage helpers
    window.saveToStorage = function(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Failed to save to storage:', error);
            return false;
        }
    };

    window.loadFromStorage = function(key) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Failed to load from storage:', error);
            return null;
        }
    };

    window.clearStorage = function(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Failed to clear storage:', error);
            return false;
        }
    };

    // Form data helpers
    window.collectFormData = function(formId) {
        const form = document.getElementById(formId);
        if (!form) return null;

        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            // Convert numeric strings to numbers
            if (!isNaN(value) && value !== '') {
                data[key] = parseFloat(value);
            } else {
                data[key] = value;
            }
        }

        return data;
    };

    window.populateForm = function(formId, data) {
        const form = document.getElementById(formId);
        if (!form || !data) return false;

        Object.keys(data).forEach(key => {
            const field = form.querySelector(`[name="${key}"], #${key}`);
            if (field) {
                field.value = data[key];
            }
        });

        return true;
    };

    // Compliance helpers
    window.calculateFAR = function(grossFloorArea, lotArea) {
        if (!lotArea || lotArea === 0) return 0;
        return grossFloorArea / lotArea;
    };

    window.calculateBuildableArea = function(lotWidth, lotDepth, setbacks = {}) {
        const frontSetback = setbacks.front || 20;
        const rearSetback = setbacks.rear || 25;
        const sideSetbacks = (setbacks.left || 6) + (setbacks.right || 6);

        const buildableWidth = Math.max(0, lotWidth - sideSetbacks);
        const buildableDepth = Math.max(0, lotDepth - frontSetback - rearSetback);

        return {
            width: buildableWidth,
            depth: buildableDepth,
            area: buildableWidth * buildableDepth
        };
    };

    window.getComplianceStatus = function(actual, required, type = 'minimum') {
        if (type === 'minimum') {
            return actual >= required;
        } else if (type === 'maximum') {
            return actual <= required;
        } else if (type === 'range') {
            return actual >= required.min && actual <= required.max;
        }
        return false;
    };

    // Export/Import functionality
    window.exportProjectData = function(data, filename = 'project-data.json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    window.importProjectData = function(callback) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = function(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const data = JSON.parse(e.target.result);
                        callback(data);
                    } catch (error) {
                        showError('Failed to parse JSON file');
                    }
                };
                reader.readAsText(file);
            }
        };
        
        input.click();
    };

    // Print functionality
    window.printResults = function(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>Housing Compliance Results</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .violation-item, .compliant-item, .warning-item { 
                            border: 1px solid #000; 
                            padding: 10px; 
                            margin: 5px 0; 
                        }
                        @media print {
                            .btn { display: none; }
                        }
                    </style>
                </head>
                <body>
                    <h1>Housing Compliance Results</h1>
                    ${element.innerHTML}
                </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    };

    // Initialize page-specific functionality
    const currentPage = window.location.pathname;
    
    if (currentPage.includes('planning')) {
        initializePlanningMode();
    } else if (currentPage.includes('validation')) {
        initializeValidationMode();
    }

    function initializePlanningMode() {
        console.log('Planning mode initialized');
        // Auto-save form data
        const form = document.getElementById('planningForm');
        if (form) {
            form.addEventListener('input', debounce(function() {
                const formData = collectFormData('planningForm');
                saveToStorage('planning_form_data', formData);
            }, 1000));

            // Load saved form data
            const savedData = loadFromStorage('planning_form_data');
            if (savedData) {
                populateForm('planningForm', savedData);
            }
        }
    }

    function initializeValidationMode() {
        console.log('Validation mode initialized');
        // Auto-save form data
        const form = document.getElementById('validationForm');
        if (form) {
            form.addEventListener('input', debounce(function() {
                const formData = collectFormData('validationForm');
                saveToStorage('validation_form_data', formData);
            }, 1000));

            // Load saved form data
            const savedData = loadFromStorage('validation_form_data');
            if (savedData) {
                populateForm('validationForm', savedData);
            }
        }
    }

    // Utility functions
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    console.log('Housing Compliance System initialized');
});
