

function init_settings(){
    
    $('.path').click(function(){
        var topBottom = $('.top, .bottom', $(this).parent())
        
        if($(this).hasClass('connected')){
            $(this).removeClass('connected box-shadow');
            topBottom.addClass('hidden');
        }else{
            $(this).addClass('connected box-shadow');
            topBottom.removeClass('hidden')
        }
    });
    var th = $(".settings th, .settings td");

    th.each(function() {
        var $this = $(this),
            n = $this.index() + 1;
        $this.hover(function() {
            var col = $("tr > td:nth-child(" + n + ")");
            col.addClass("hovered");
        }, function(){
            th.removeClass('hovered')
        });
    });
    
    
    if(!$('.nav.nav-list a[href="'+decodeURIComponent(window.location.hash)+'"]').tab('show').length)
        $('.nav.nav-list a[data-toggle="tab"]:first').tab('show')

    $('.control-group.path input').each(function(key, item){
        $(item).fileBrowser({ title: 'Select Folder', key: 'postprocessPath', showFiles: false});
    });
    $('.control-group.filepath input').each(function(key, item){
        $(item).fileBrowser({ title: 'Select File', key: 'postprocessPath', showFiles: true});
    });

    // i cant get the tooltip data api to work so we do a jquery
    $("input").tooltip({
        'selector': '',
        'placement': 'right'
     })
    
    $('input[type="checkbox"][data-configname="enabled"]').change(function(event){
        var icon = $('.nav.nav-list a[href="#'+$(this).data('belongsto')+'"] i')
        if($(this).prop('checked')){
            icon.removeClass('rotateIn').addClass('animated rotateOut')
        }else{
            icon.removeClass('rotateOut').addClass('animated rotateIn icon-off')
       }
    });
    $("input.newInstance").click(function(){
        if( $(this).prev('input').val() )
                document.location = webRoot+'/createInstance?plugin=' + encodeURIComponent($(this).data('plugin')) + '&instance=' + encodeURIComponent($(this).prev('input').val())
        else
            $(this).prev('input').stop().css("background-color", "#FFFF9C").animate({ backgroundColor: "#FFFFFF"}, 1500);
    });
    $("input.newInstanceName").keypress(function(event){
        var regex = new RegExp("^[a-zA-Z0-9_]+$");
        var key = String.fromCharCode(!event.charCode ? event.which : event.charCode);
        if (!regex.test(key)) {
           event.preventDefault();
           return false;
        }
    });
    $('.nav.nav-list a').hover(function(){
        var t = $($(this).attr('href'))
        $('.nav.nav-list.MediaTypeManager a').each(function(k,i){
            var id = $(i).attr('href').replace('#', '');
            var input = $('input[name$="'+id+'_runfor"][type="checkbox"]',t)
                if(input.prop('checked')){
                    $(i).addClass('btn-striped animate btn-success')
                }

            var notice = $('span[title="'+$(i).data('identifier')+'"].support-for-mediatype', t);
            if(notice.length)
                $(i).addClass('btn-striped animate btn-info')
            
        });
        $('.nav.nav-list.DownloadType a').each(function(k,i){
            var id = $(i).data('identifier');
            var notice = $('span[title="'+id+'"].download-type-extension', t)
            if(notice.length)
                $(i).addClass('btn-striped animate btn-info')
            
            
        });

    },function(){
        $('.nav.nav-list.MediaTypeManager a').removeClass('btn-striped animate btn-success btn-info')
        $('.nav.nav-list.DownloadType a').removeClass('btn-striped animate btn-info')

    });

    labelInputConnector($('label'));

    $('.nav.nav-list a[data-toggle="tab"]').on('show', function (e) {
        var t = $(e.target)
        var tab = $(t.attr('href'));
        $('.nav.nav-list li').removeClass('active');
        $(this).parent().addClass('active');
        window.location.hash = t.attr('href');
    })
    
    $( ".nav-list" ).sortable({
        stop: function(event, ui) {
            $('.nav.nav-list a[data-toggle="tab"]').each(function(k,i){
                var input = $('input[name=' + $(i).data('type') + '-' + $(i).data('instance') + '-plugin_order]').val(k);
                console.log($(i).data('type') + '-' + $(i).data('instance'), "is now order", k);
            })
        }
    });
    
    $("input.removeInstance").click(function(){       
        document.location = webRoot+'/removeInstance?plugin=' + $(this).data('plugin') + '&instance=' + $(this).data('instance')
    });

    
    $('input[type="submit"]').click(function(event){
        console.log(this)
        if($(this).hasClass('animate')){
            event.preventDefault();
            return false;
        }else if($(this).hasClass('btn-warning')){
            return true;
        }
        event.preventDefault();
        
        saveButtons = $('input[type="submit"]')
        saveButtons.addClass('btn-striped animate')
        data = $('.tab-pane.active input, .tab-pane.active select, input.plugin_order, .wizard-main.well #theSettingsForm').serialize()
        
        console.log($('.tab-pane.active input, input.plugin_order'), data);
        
        $.post(webRoot+'/ajax/save', data, function(res, textStatus) {
            if(res['result']){
                $(this).button('loading');
                noty({text: res['msg'], type: 'success', timeout: 1000})
            }else{
                noty({text: res['msg'], type: 'error'})  
                saveButtons.addClass('btn-warning')
            }
            saveButtons.removeClass('btn-striped animate')
        }, "json").error(function(){
            noty({text: 'Server error. Is it running? Check logs', type: 'error'}) 
            saveButtons.removeClass('animate btn-success').addClass('btn-warning')
        });

    });
};

