

$(document).ready(function() {
    
    $("#container").addClass('wizard');
    
    $("#content").on('click', "a[data-next]", function(event){
        var link = $(this).attr('href')
        var step = $(this).data('step')
        $('#content').addClass('animated fadeOutLeft').removeClass('fadeOutRight fadeInRight fadeInLeft')
        window.setTimeout(function(){
            $('#content').load(link + ' #content', function() {
                window.history.pushState({}, "another step", link);
                $('#content').removeClass('fadeOutLeft').addClass('animated fadeInRight');
                $("#container").removeClass().addClass('wizard');
                runStepFn(step)
            });
        }, 800)
        event.preventDefault()
    });
    $("#content").on('click', "a[data-prev]", function(event){
        var link = $(this).attr('href')
        var step = $(this).data('step')
        $('#content').addClass('animated fadeOutRight').removeClass('fadeOutLeft fadeInLeft fadeInRight')
        window.setTimeout(function(){
            $('#content').load(link + ' #content', function() {
                window.history.pushState({}, "another step", link);
                $('#content').removeClass('fadeOutRight').addClass('animated fadeInLeft');
                $("#container").removeClass().addClass('wizard');
                runStepFn(step)
            });
        }, 800)
        event.preventDefault()
    });
    runCurStepFn();
});

runStepFn = function(step){
    try{
        var fn = window['step_'+step];
        fn();
    }catch (e) {
        console.log(step, e)
    }
}

runCurStepFn = function(){ 
    runStepFn(getCurStep())
}

getCurStep = function(){
    var url = window.location + ''
    return url.match(/wizard\/(\d+)/)[1];    
}

step_1 = function(){
    $('#container').addClass('settings')
    init_settings();
}

step_2 = function(){
    ajaxRepo();
    $('#container').addClass('plugins')
}

step_3 = function(){
    var data = {1: 'getDownloaders',
            2: 'getIndexers',
            3: 'getNotifiers',
            4: 'getProvider',
            5: 'getMediaTypeManager'}
    $('#settings-in-here').load(webRoot +'/settings/?'+ $.param(data) + ' #content', function() {
        init_settings();
        $.get(webRoot +'/settingsPluginHtml/?'+ $.param(data), function(data, status){
            console.log(data);
            $('head').append(data);
        });
        
    });
    $('#container').addClass('settings')
    $('#content > .wizard-main.well').removeClass('well')
}

step_finished = function(){
    $('#container').removeClass('wizard')
}