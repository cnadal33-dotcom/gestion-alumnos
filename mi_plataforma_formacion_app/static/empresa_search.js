// Autocomplete para empresa en el filtro de la página de inicio
// Requiere que la variable window.empresas esté disponible con [{id, nombre}]
document.addEventListener('DOMContentLoaded', function() {
  var input = document.getElementById('empresa_search');
  var datalist = document.getElementById('empresas_datalist');
  if (!input || !datalist || !window.empresas) return;

  input.addEventListener('input', function() {
    var val = this.value.toLowerCase();
    datalist.innerHTML = '';
    window.empresas.forEach(function(empresa) {
      if (empresa.nombre.toLowerCase().includes(val)) {
        var option = document.createElement('option');
        option.value = empresa.nombre;
        datalist.appendChild(option);
      }
    });
  });
});
