// Minimal JS for interactive manager UI
document.addEventListener('DOMContentLoaded', function(){
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar-wrapper');

  if(toggle && sidebar){
    toggle.addEventListener('click', function(e){
      e.preventDefault();
      if(window.innerWidth <= 768){
        sidebar.classList.toggle('open');
      } else {
        document.body.classList.toggle('sidebar-collapsed');
        sidebar.style.width = document.body.classList.contains('sidebar-collapsed') ? '80px' : '250px';
      }
    });

    // Close sidebar on click outside (mobile)
    document.addEventListener('click', function(e){
      if(window.innerWidth <= 768 && sidebar.classList.contains('open')){
        if(!sidebar.contains(e.target) && e.target.id !== 'sidebarToggle'){
          sidebar.classList.remove('open');
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
        if(!ids.length){ alert('Select atleast one item to export'); return; }
        const params = new URLSearchParams();
        ids.forEach(i => params.append('id', i));
        window.location = window.location.pathname + 'export/?' + params.toString();
      });
    }

    if(bulkDelete){
      bulkDelete.addEventListener('click', function(e){
        e.preventDefault();
        const ids = getSelectedIds();
        if(!ids.length){ alert('Select atleast one item to delete'); return; }
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
});
