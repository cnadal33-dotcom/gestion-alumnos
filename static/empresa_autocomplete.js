$(function() {
  $("#input-empresa").autocomplete({
    minLength: 2,
    source: function(request, response) {
      $.getJSON("/api/empresas_autocomplete", { q: request.term }, function(data) {
        response($.map(data, function(item) {
          return {
            label: item.nombre,
            value: item.nombre,
            id: item.id
          };
        }));
      });
    },
    select: function(event, ui) {
      $("#input-empresa").val(ui.item.label);
      $("#empresa_id_hidden").val(ui.item.id);
      return false;
    }
  });
});
