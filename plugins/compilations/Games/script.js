
$(document).ready(function() {
    de_lad1337_games_init();
});


function de_lad1337_games_init(){

    $('.de-lad1337-games .tabbable .tab-pane').each(function(index, item){
        $(item).appendTo(".de-lad1337-games .tab-content");
        $(item).removeClass('hidden');
    });
    
    $(".de-lad1337-games a.trailer").YouTubePopup({'clickOutsideClose':true, 'hideTitleBar':true});
     
}