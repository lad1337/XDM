

function ajaxRepoRecache(){
    $('.repo-container .progress').show("slide", { direction: "up" }, 500)
    $('.repo-container .inner').hide("slide", { direction: "up" }, 500)

    jQuery.get( webRoot+'/plugins', {'recache': 1});
    window.setTimeout(function(){ajaxRepo()}, 1000);
}

function ajaxRepo(){
    var sort_mode = $("#plugin-type-select a.active").data("type");
    if(!sort_mode)
        sort_mode = "type";
    jQuery.get( webRoot+'/ajax/plugins_by_'+sort_mode, {}, function(res){
        if(!res){
            console.log('retrying')
            window.setTimeout(function() {ajaxRepo()}, 1000);
            return
        }
        $('.repo-container .inner').html(res)
        $('.repo-container .progress').hide("slide", { direction: "up" }, 500)
        $('.repo-container .inner').show("slide", { direction: "up" }, 500)
    });
};


function checkAndSetup(button){
    console.log('checkAndSetup', button)
    var b = $(button);
    b.removeClass('btn-striped animate')
    //http://stackoverflow.com/questions/2723140/validating-url-with-jquery-without-the-validate-plugin
    var url = b.siblings('input').val();
    if(!/^([a-z]([a-z]|\d|\+|-|\.)*):(\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?((\[(|(v[\da-f]{1,}\.(([a-z]|\d|-|\.|_|~)|[!\$&'\(\)\*\+,;=]|:)+))\])|((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=])*)(:\d*)?)(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*|(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)|((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)|((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)){0})(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i.test(url)) {
        b.siblings('input').stop().css("background-color", "#FFFF9C").animate({ backgroundColor: "#FFFFFF"}, 1500);
        return false;
    }
    b.attr('data-url', url)
    return true;
    
} 

function addRepo(button){
    $('.repo-container .progress').show("slide", { direction: "up" }, 500)
    $('.repo-container .inner').hide("slide", { direction: "up" }, 500)
    var url = $(button).data('url')
    if(url){
        jQuery.get( webRoot+'/ajax/addRepo', {'url': url}, function(res){
            ajaxRepo();
        });
    }
}
function removeRepo(button){
    $('.repo-container .progress').show("slide", { direction: "up" }, 500)
    $('.repo-container .inner').hide("slide", { direction: "up" }, 500)
    var url = $(button).data('url')
    if(url){
        jQuery.get( webRoot+'/ajax/removeRepo', {'url': url}, function(res){
            ajaxRepo();
        });
    }
}

function installModalFromUrl(button){
    $(button).attr('data-download', url)
    var modal = installModal(button)
    return false;
}

var firstMessage = true;

function deinstallModal(button){
    id = $(button).data('identifier');
    data = {'identifier': id}
    name = 'Deinstalling '+id
    var frame = ajaxModal(button, name, webRoot+'/ajax/deinstallPlugin', data)
    
    firstMessage = true;        
    window.setTimeout(function(){messageScrobbler('getRepoMessage')}, 500);
    $('.modal-body', frame).css('padding', 0)
    $('.modal-header .close').remove()
    return false;
}

function selectedInstallModal(button){
    var data = {}
    $('.repo-container .btn-info input:checked').each(function(index,item){
        data[index] = $(item).data('identifier')
    });
    
    name = 'Installing plugins'
    var frame = ajaxModal(button, name, webRoot+'/ajax/installPlugins', data)
    
    firstMessage = true;        
    window.setTimeout(function(){messageScrobbler('getRepoMessage')}, 500);
    $('.modal-body', frame).css('padding', 0)
    $('.modal-header .close').remove()
    return false;
}



$(document).ready(function() {
    window.setTimeout(function(){ajaxRepo()}, 1000);
    $('.progress .bar').resize(function(event){
        $('span', this).width($(this).parent().width())
        $('span', $(this).parent()).css('line-height', $(this).parent().height()+'px')
    });
    $('.progress .bar').resize()
});

