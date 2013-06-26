
$(document).ready(function() {

    $('.de-lad1337-games .tabbable .tab-pane').each(function(index, item){
        $(item).appendTo(".de-lad1337-games .tab-content");
        $(item).removeClass('hidden');
    });
    
});
