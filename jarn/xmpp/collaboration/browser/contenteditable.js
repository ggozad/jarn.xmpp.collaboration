$('#editor').live('focus', function() {
  before = $(this).html();
}).live('blur keyup paste', function() { 
  if (before != $(this).html()) { $(this).trigger('change'); }
});

$('#editor').live('change', function() {alert('changed')});
