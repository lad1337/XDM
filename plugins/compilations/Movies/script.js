
$(document).ready(function() {
    $(".de-lad1337-movies a.trailer").YouTubePopup({'clickOutsideClose':true, 'hideTitleBar':true});

    $('.de-lad1337-movies').on('click', '.movie img', function(){
        console.log(this)
        var p = $(this).parent().parent();
        $('.de-lad1337-movies .movie').removeClass('active')
        $('.de-lad1337-movies .overview').popover('hide')
        if(!p.hasClass('active')){
            p.addClass('active');
        }
    });
    
    $('.de-lad1337-movies').on('click', '.inner i.icon-remove', function(){
        $('.de-lad1337-movies .movie').removeClass('active')
        $('.de-lad1337-movies .overview').popover('hide')
    });
    
    
    $('.de-lad1337-movies .overview').popover()
});
