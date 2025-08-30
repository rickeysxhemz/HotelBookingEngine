// Enhanced JS for interactive manager UI with form improvements
document.addEventListener('DOMContentLoaded', function(){
  // Sidebar functionality
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar-wrapper');

  if(toggle && sidebar){
    toggle.addEventListener('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      
      if(window.innerWidth <= 768){
        sidebar.classList.toggle('open');
        // Toggle burger menu icon
        const icon = toggle.querySelector('i');
        const overlay = document.querySelector('.sidebar-overlay');
        
        if (sidebar.classList.contains('open')) {
          icon.classList.remove('fa-bars');
          icon.classList.add('fa-times');
          if (overlay) overlay.style.display = 'block';
        } else {
          icon.classList.remove('fa-times');
          icon.classList.add('fa-bars');
          if (overlay) overlay.style.display = 'none';
        }
      } else {
        document.body.classList.toggle('sidebar-collapsed');
        sidebar.style.width = document.body.classList.contains('sidebar-collapsed') ? '80px' : '250px';
      }
    });

    // Close sidebar on click outside (mobile)
    document.addEventListener('click', function(e){
      if(window.innerWidth <= 768 && sidebar.classList.contains('open')){
        if(!sidebar.contains(e.target) && e.target.id !== 'sidebarToggle' && !toggle.contains(e.target)){
          sidebar.classList.remove('open');
          const icon = toggle.querySelector('i');
          const overlay = document.querySelector('.sidebar-overlay');
          icon.classList.remove('fa-times');
          icon.classList.add('fa-bars');
          if (overlay) overlay.style.display = 'none';
        }
      }
    });

    // Close sidebar when overlay is clicked
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
      overlay.addEventListener('click', function() {
        sidebar.classList.remove('open');
        const icon = toggle.querySelector('i');
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
        overlay.style.display = 'none';
      });
    }

    // Close sidebar on escape key
    document.addEventListener('keydown', function(e){
      if(e.key === 'Escape' && window.innerWidth <= 768 && sidebar.classList.contains('open')){
        sidebar.classList.remove('open');
        const icon = toggle.querySelector('i');
        const overlay = document.querySelector('.sidebar-overlay');
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
        if (overlay) overlay.style.display = 'none';
      }
    });
  }
  
  // Mobile search functionality
  const mobileSearchToggle = document.getElementById('mobileSearchToggle');
  if (mobileSearchToggle) {
    mobileSearchToggle.addEventListener('click', function() {
      // Create mobile search overlay if it doesn't exist
      let mobileSearchOverlay = document.getElementById('mobileSearchOverlay');
      if (!mobileSearchOverlay) {
        mobileSearchOverlay = document.createElement('div');
        mobileSearchOverlay.id = 'mobileSearchOverlay';
        mobileSearchOverlay.style.cssText = `
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0,0,0,0.8);
          z-index: 1050;
          display: none;
          align-items: flex-start;
          justify-content: center;
          padding-top: 80px;
        `;
        
        const searchForm = document.createElement('form');
        searchForm.method = 'get';
        searchForm.action = "/manager/search/";
        searchForm.style.cssText = `
          background: white;
          padding: 20px;
          border-radius: 8px;
          width: 90%;
          max-width: 400px;
          position: relative;
        `;
        
        const searchInput = document.createElement('input');
        searchInput.type = 'search';
        searchInput.name = 'q';
        searchInput.placeholder = 'Search across all entities...';
        searchInput.required = true;
        searchInput.style.cssText = `
          width: 100%;
          padding: 12px;
          border: 2px solid #007bff;
          border-radius: 6px;
          font-size: 16px;
          margin-bottom: 10px;
        `;
        
        const searchButton = document.createElement('button');
        searchButton.type = 'submit';
        searchButton.innerHTML = '<i class="fas fa-search me-2"></i> Search';
        searchButton.style.cssText = `
          width: 100%;
          padding: 12px;
          background: #007bff;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 16px;
          cursor: pointer;
        `;
        
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.innerHTML = '<i class="fas fa-times"></i>';
        closeButton.style.cssText = `
          position: absolute;
          top: 10px;
          right: 10px;
          background: none;
          border: none;
          font-size: 18px;
          color: #666;
          cursor: pointer;
        `;
        
        closeButton.addEventListener('click', function() {
          mobileSearchOverlay.style.display = 'none';
        });
        
        searchForm.appendChild(closeButton);
        searchForm.appendChild(searchInput);
        searchForm.appendChild(searchButton);
        mobileSearchOverlay.appendChild(searchForm);
        document.body.appendChild(mobileSearchOverlay);
        
        // Close on overlay click (outside form)
        mobileSearchOverlay.addEventListener('click', function(e) {
          if (e.target === mobileSearchOverlay) {
            mobileSearchOverlay.style.display = 'none';
          }
        });
        
        // Close on escape key
        document.addEventListener('keydown', function(e) {
          if (e.key === 'Escape' && mobileSearchOverlay.style.display === 'flex') {
            mobileSearchOverlay.style.display = 'none';
          }
        });
      }
      
      // Toggle overlay
      mobileSearchOverlay.style.display = mobileSearchOverlay.style.display === 'flex' ? 'none' : 'flex';
      
      // Focus input when shown
      if (mobileSearchOverlay.style.display === 'flex') {
        const input = mobileSearchOverlay.querySelector('input');
        if (input) {
          setTimeout(() => input.focus(), 100);
        }
      }
    });
  }

  // Bulk actions
  const selectAll = document.getElementById('selectAll');
  if(selectAll){
    selectAll.addEventListener('change', function(){
      document.querySelectorAll('.row-checkbox').forEach(cb => cb.checked = selectAll.checked);
    });

    const bulkExport = document.getElementById('bulkExport');
    const bulkDelete = document.getElementById('bulkDelete');

    function getSelectedIds(){
      return Array.from(document.querySelectorAll('.row-checkbox:checked')).map(i => i.value);
    }

    if(bulkExport){
      bulkExport.addEventListener('click', function(e){
        e.preventDefault();
        const ids = getSelectedIds();
        if(!ids.length){ alert('Select at least one item to export'); return; }
        const params = new URLSearchParams();
        ids.forEach(i => params.append('id', i));
        window.location = window.location.pathname + 'export/?' + params.toString();
      });
    }

    if(bulkDelete){
      bulkDelete.addEventListener('click', function(e){
        e.preventDefault();
        const ids = getSelectedIds();
        if(!ids.length){ alert('Select at least one item to delete'); return; }
        if(!confirm('Delete selected items? This cannot be undone.')) return;
        fetch(window.location.pathname + 'bulk-delete/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
          body: JSON.stringify({ ids })
        }).then(r => {
          if(r.ok) location.reload(); else alert('Failed to delete');
        });
      });
    }

    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = cookies[i].trim();
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
    }
  }

  // Enhanced Form Functionality
  enhanceForms();

  // Real-time form validation
  setupFormValidation();

  // Auto-focus first form field
  autoFocusFirstField();

  // Form submission improvements
  enhanceFormSubmissions();
});

// Enhanced form functionality
function enhanceForms() {
  // Add input masking for phone numbers
  const phoneInputs = document.querySelectorAll('input[type="tel"], input[name*="phone"]');
  phoneInputs.forEach(input => {
    input.addEventListener('input', function(e) {
      const value = e.target.value.replace(/\D/g, '');
      if (value.length > 10) {
        e.target.value = value.slice(0, 10);
      }
    });
  });

  // Currency formatting for price fields
  const priceInputs = document.querySelectorAll('input[name*="price"], input[name*="charge"]');
  priceInputs.forEach(input => {
    input.addEventListener('blur', function(e) {
      const value = parseFloat(e.target.value);
      if (!isNaN(value)) {
        e.target.value = value.toFixed(2);
      }
    });
  });

  // Character counters for textareas
  const textareas = document.querySelectorAll('textarea[maxlength]');
  textareas.forEach(textarea => {
    const maxLength = parseInt(textarea.getAttribute('maxlength'));
    const counter = document.createElement('div');
    counter.className = 'form-text character-counter';
    counter.style.fontSize = '0.8rem';
    textarea.parentNode.appendChild(counter);
    
    const updateCounter = () => {
      const remaining = maxLength - textarea.value.length;
      counter.textContent = `${remaining} characters remaining`;
      counter.style.color = remaining < 20 ? '#dc3545' : '#64748b';
    };
    
    textarea.addEventListener('input', updateCounter);
    updateCounter();
  });

  // Enhanced date inputs
  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(input => {
    input.addEventListener('focus', function() {
      this.showPicker?.();
    });
  });

  // Auto-advance form fields
  setupAutoAdvance();

  // Enhanced file upload with image preview
  setupFileUploads();
}

// Form validation setup
function setupFormValidation() {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
      // Real-time validation
      input.addEventListener('blur', function() {
        validateField(this);
      });
      
      // Clear validation on focus
      input.addEventListener('focus', function() {
        this.classList.remove('is-invalid');
        const feedback = this.nextElementSibling;
        if (feedback && feedback.classList.contains('invalid-feedback')) {
          feedback.remove();
        }
      });
    });

    // Enhanced form submission
    form.addEventListener('submit', function(e) {
      if (!validateForm(this)) {
        e.preventDefault();
        // Scroll to first error
        const firstError = this.querySelector('.is-invalid');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
          firstError.focus();
        }
      }
    });
  });
}

// Field validation
function validateField(field) {
  const value = field.value.trim();
  const isRequired = field.hasAttribute('required');
  const minLength = field.getAttribute('minlength');
  const maxLength = field.getAttribute('maxlength');
  const pattern = field.getAttribute('pattern');
  
  let isValid = true;
  let errorMessage = '';

  // Required field validation
  if (isRequired && !value) {
    isValid = false;
    errorMessage = 'This field is required';
  }

  // Length validation
  if (isValid && value) {
    if (minLength && value.length < parseInt(minLength)) {
      isValid = false;
      errorMessage = `Minimum ${minLength} characters required`;
    }
    if (maxLength && value.length > parseInt(maxLength)) {
      isValid = false;
      errorMessage = `Maximum ${maxLength} characters allowed`;
    }
  }

  // Pattern validation
  if (isValid && value && pattern) {
    const regex = new RegExp(pattern);
    if (!regex.test(value)) {
      isValid = false;
      errorMessage = 'Invalid format';
    }
  }

  // Email validation
  if (isValid && field.type === 'email' && value) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      isValid = false;
      errorMessage = 'Please enter a valid email address';
    }
  }

  // Update field state
  if (!isValid) {
    field.classList.add('is-invalid');
    field.classList.remove('is-valid');
    
    // Add or update error message
    let feedback = field.nextElementSibling;
    if (!feedback || !feedback.classList.contains('invalid-feedback')) {
      feedback = document.createElement('div');
      feedback.className = 'invalid-feedback';
      field.parentNode.appendChild(feedback);
    }
    feedback.textContent = errorMessage;
  } else {
    field.classList.remove('is-invalid');
    field.classList.add('is-valid');
  }

  return isValid;
}

// Form validation
function validateForm(form) {
  let isValid = true;
  const inputs = form.querySelectorAll('input, select, textarea');
  
  inputs.forEach(input => {
    if (!validateField(input)) {
      isValid = false;
    }
  });

  return isValid;
}

// Auto-focus first field
function autoFocusFirstField() {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    const firstField = form.querySelector('input, select, textarea');
    if (firstField && !firstField.disabled) {
      setTimeout(() => firstField.focus(), 100);
    }
  });
}

// Auto-advance between fields
function setupAutoAdvance() {
  const inputs = document.querySelectorAll('input[maxlength]');
  inputs.forEach(input => {
    input.addEventListener('input', function(e) {
      const maxLength = parseInt(this.getAttribute('maxlength'));
      if (this.value.length === maxLength) {
        const nextInput = this.nextElementSibling;
        if (nextInput && (nextInput.tagName === 'INPUT' || nextInput.tagName === 'SELECT' || nextInput.tagName === 'TEXTAREA')) {
          nextInput.focus();
        }
      }
    });
  });
}

// Enhanced form submissions
function enhanceFormSubmissions() {
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    if (submitButton) {
      form.addEventListener('submit', function() {
        // Disable submit button to prevent double submissions
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        
        // Add loading state to form
        form.classList.add('form-submitting');
      });
    }
  });
}

// Utility function to format phone numbers
function formatPhoneNumber(phone) {
  const cleaned = ('' + phone).replace(/\D/g, '');
  const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
  if (match) {
    return '(' + match[1] + ') ' + match[2] + '-' + match[3];
  }
  return phone;
}

// Utility function to format currency
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
}

// Enhanced file upload with image preview
function setupFileUploads() {
  const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
  
  fileInputs.forEach(input => {
    // Create preview container
    const previewContainer = document.createElement('div');
    previewContainer.className = 'file-preview';
    previewContainer.style.cssText = `
      margin-top: 0.5rem;
      padding: 1rem;
      background-color: var(--light);
      border-radius: 0.375rem;
      border: 1px solid var(--border);
      display: none;
    `;
    
    const previewImage = document.createElement('img');
    previewImage.style.cssText = `
      max-width: 100%;
      height: auto;
      border-radius: 0.25rem;
      display: none;
    `;
    
    const previewText = document.createElement('div');
    previewText.className = 'form-text';
    previewText.textContent = 'No image selected';
    
    previewContainer.appendChild(previewImage);
    previewContainer.appendChild(previewText);
    input.parentNode.appendChild(previewContainer);
    
    // Handle file selection
    input.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        if (file.type.startsWith('image/')) {
          const reader = new FileReader();
          
          reader.onload = function(e) {
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
            previewText.style.display = 'none';
            previewContainer.style.display = 'block';
            
            // Add remove button
            let removeBtn = previewContainer.querySelector('.remove-image');
            if (!removeBtn) {
              removeBtn = document.createElement('button');
              removeBtn.className = 'btn btn-sm btn-outline-danger remove-image';
              removeBtn.innerHTML = '<i class="fas fa-times"></i> Remove';
              removeBtn.style.marginTop = '0.5rem';
              removeBtn.addEventListener('click', function() {
                input.value = '';
                previewImage.style.display = 'none';
                previewText.style.display = 'block';
                previewContainer.style.display = 'none';
              });
              previewContainer.appendChild(removeBtn);
            }
          };
          
          reader.readAsDataURL(file);
        } else {
          alert('Please select an image file');
          input.value = '';
        }
      } else {
        previewImage.style.display = 'none';
        previewText.style.display = 'block';
        previewContainer.style.display = 'none';
      }
    });
    
    // Drag and drop functionality
    const formGroup = input.closest('.form-group') || input.parentNode;
    formGroup.addEventListener('dragover', function(e) {
      e.preventDefault();
      formGroup.style.borderColor = 'var(--amber-500)';
      formGroup.style.backgroundColor = 'var(--amber-50)';
    });
    
    formGroup.addEventListener('dragleave', function(e) {
      e.preventDefault();
      formGroup.style.borderColor = '';
      formGroup.style.backgroundColor = '';
    });
    
    formGroup.addEventListener('drop', function(e) {
      e.preventDefault();
      formGroup.style.borderColor = '';
      formGroup.style.backgroundColor = '';
      
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        input.files = files;
        input.dispatchEvent(new Event('change'));
      }
    });
  });
  
  // Multiple file upload support
  const multiFileInputs = document.querySelectorAll('input[type="file"][multiple]');
  multiFileInputs.forEach(input => {
    input.addEventListener('change', function(e) {
      const files = e.target.files;
      if (files.length > 0) {
        const fileList = document.createElement('div');
        fileList.className = 'file-list';
        fileList.style.cssText = `
          margin-top: 0.5rem;
          padding: 0.5rem;
          background-color: var(--light);
          border-radius: 0.375rem;
          border: 1px solid var(--border);
        `;
        
        Array.from(files).forEach((file, index) => {
          const fileItem = document.createElement('div');
          fileItem.className = 'file-item';
          fileItem.style.cssText = `
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.25rem;
            margin-bottom: 0.25rem;
          `;
          
          const fileName = document.createElement('span');
          fileName.textContent = file.name;
          fileName.style.fontSize = '0.9rem';
          
          const fileSize = document.createElement('span');
          fileSize.textContent = formatFileSize(file.size);
          fileSize.style.fontSize = '0.8rem';
          fileSize.style.color = 'var(--muted)';
          
          fileItem.appendChild(fileName);
          fileItem.appendChild(fileSize);
          fileList.appendChild(fileItem);
        });
        
        // Remove existing file list if any
        const existingList = input.parentNode.querySelector('.file-list');
        if (existingList) {
          existingList.remove();
        }
        
        input.parentNode.appendChild(fileList);
      }
    });
  });
}

// Utility function to format file size
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
