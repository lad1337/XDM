

var playPath = 'M11.166,23.963L22.359,17.5c1.43-0.824,1.43-2.175,0-3L11.166,8.037c-1.429-0.826-2.598-0.15-2.598,1.5v12.926C8.568,24.113,9.737,24.789,11.166,23.963z';
var playPathS = 'M84.23,73H17.968C8.91,73,1.54,65.63,1.54,56.571V20.429C1.54,11.37,8.91,4,17.968,4H84.23   c9.059,0,16.428,7.37,16.428,16.429v36.143C100.658,65.63,93.289,73,84.23,73z M17.968,13.857c-3.624,0-6.571,2.948-6.571,6.571   v36.143c0,3.624,2.948,6.571,6.571,6.571H84.23c3.623,0,6.571-2.947,6.571-6.571V20.429c0-3.624-2.948-6.571-6.571-6.571H17.968z'
var playPathS2 = 'M42.611,23.34c0-1.344,0.898-1.809,1.995-1.029l20.802,14.774c1.096,0.779,1.096,2.053,0,2.832L44.605,54.69  c-1.097,0.778-1.995,0.315-1.995-1.031V23.34z'
    
$(document).ready(function() {
    $(".youtube").youtube();
    $(".youtube").fancybox({
        openEffect  : 'none',
        closeEffect : 'none',
        nextEffect  : 'none',
        prevEffect  : 'none',
        padding     : 0,
        margin      : [20, 60, 20, 60] // Increase left/right margin
    });

    
    $('.navbar .navbar-search .add-on').click(function(){
        $(this).siblings('input').val('')
    })
    
    $('.navbar .navbar-search input').typeahead({
        source: function (term, query) {
            autoCompl = []
            // see web.py for the mediatypenames and 'All' handling
            // see base.html for the js var mediaTypenames
            $.each(mediaTypenames, function(index, item){
                autoCompl.push(item + ': ' + term);
            });
            // searching for all creates locked databases because of the two threads
            // disableling that for now
            // autoCompl.push('All: ' + term);
            return autoCompl;
        },
        sorter: function (items) {
            return items;
        },
        highlighter: function (item) {
            var regex = new RegExp( ': (' + this.query + ')', 'gi' );
            return item.replace( regex, ": <strong>$1</strong>" );
        },
        //http://stackoverflow.com/questions/9425024/submit-selection-on-bootstrap-typeahead-autocomplete
        updater : function(item) {
            this.$element[0].value = item;
            this.$element[0].form.submit();
            return item;
        }
    })
    $('.navbar .dropdown-toggle').dropdown()

    
});

function ajaxDeleteElement(id, deleteNode){
    data = {};
    data['id'] = id;
    $.getJSON('/ajaxDeleteElement', data, function(res){
        if(res['result']){
            deleteNode.hide('slow')
            noty({text: res['msg'], type: 'success', timeout:2000})
        }
    })
};


function createModal(name){
    var id = name+'Frame';
    var modalFrame = $('#'+id);
    
    modalFrame.remove()
    // set up the bootstrap dialog
    modalFrame = $('<div id="'+id+'" class="modal hide fade modal-wide"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button><h3>'+name+'</h3></div><div class="modal-body"></div></div>').appendTo('body')
    modalFrame.append('<div class="modal-footer"><button class="btn" data-dismiss="modal">Close</button></div>')
    
    var otherOpenModals = $('body>div.modal:not([style="display: none;"]):not(#'+id+')').modal('hide')
    console.log(otherOpenModals)
    $('body').append(modalFrame)
    if(otherOpenModals.length){
        $('[data-dismiss="modal"]', modalFrame).click(function(e){
            otherOpenModals.modal('show')
        });
        $('.modal-footer button:first',modalFrame).text('Back')
    }
    return modalFrame
}

function ajaxModal(sender, name, url, data){
    $(sender).addClass('btn-striped animate');
    var myModal = createModal(name)
    $.post(url, data, function(res){
        $('.modal-body', myModal).html(res)
        myModal.modal();
        $(sender).removeClass('btn-striped animate');
    });
    return myModal;
}


function showEvents(sender, id){
    data = {'id': id}
    name = 'Events'
    var myModal = ajaxModal(sender, name, '/ajaxGetEventsFrame', data)
    // check for events
    if(!$('.modal-body tr:not(.notice)', myModal).length)
        $('.modal-footer', myModal).append('<input class="btn btn-warning" value="Clear Events" type="submit"></div>')
    //hook up the clear event button
    $('input[type="submit"]', myModal).click(function(e){
        var t = $(this);
        t.addClass('btn-striped animate')
        $.getJSON('/ajaxClearEvents', data, function(res){
            if(res['result']){
                noty({text: res['msg'], type: 'success', timeout: 1000})
                $('.modal-body', myModal).html('<h4>No events yet.</h4>')
            }else{
                noty({text: res['msg'], type: 'error'})  
                saveButtons.addClass('btn-warning')
            }
            t.removeClass('btn-striped animate')
        }).error(function(){
            noty({text: 'Server error. Is it running? Check logs', type: 'error'}) 
            t.removeClass('animate')
        })
    })
}

function showDownlads(sender, id){
    data = {'id': id}
    name = 'Downloads'
    ajaxModal(sender, name, '/ajaxGetDownloadsFrame', data)
}

function showConfigs(sender, id){
    data = {'id': id}
    name = 'Configuration'
    var myModal = ajaxModal(sender, name, '/ajaxGetConfigFrame', data)
    
    $('.modal-footer', myModal).append('<input class="btn btn-success" value="Save" type="submit"></div>')
    window.setTimeout(function(){
        console.log('myModal', myModal[0])
        console.log('tab as', $('.nav-tabs a[data-toggle="tab"]:first'))
        console.log($('.nav-tabs a[data-toggle="tab"]:first', myModal))
        $('.nav-tabs a[data-toggle="tab"]:first', myModal).tab('show')
        formAjaxSaveConnect($('input[type="submit"]', myModal), $('#config-'+id))
    }, 1000);

}

function labelInputConnector(labels){
    labels.each(function(){
        var curLabel = $(this);
        var curInput = $('input[type!="hidden"]', curLabel.parent());
        // check for the for attr to not beeing invasive
        if(typeof(curLabel.attr('for')) == "undefined" && curInput.length){
            var id = curInput.attr('id');
            if(!id){
                // remove "0." from the random to get ids without a dot
                id = $.now()+((''+Math.random()).split('.')[1]);
                curInput.attr('id',id);
            }
            curLabel.attr('for',id);
        }
    });
}



function formAjaxSaveConnect(saveButtons, theForm){
    saveButtons.click(function(event){
        console.log(this)
        if($(this).hasClass('animate')){
            event.preventDefault();
            return false;
        }else if($(this).hasClass('btn-warning')){
            return true;
        }
        event.preventDefault();
        
        saveButtons.addClass('btn-striped animate')
        data = theForm.serialize()
        

        $.getJSON('/ajaxSave', data, function(res){
            if(res['result']){
                $(this).button('loading');
                noty({text: res['msg'], type: 'success', timeout: 1000})
            }else{
                noty({text: res['msg'], type: 'error'})  
                saveButtons.addClass('btn-warning')
            }
            saveButtons.removeClass('btn-striped animate')
        }).error(function(){
            noty({text: 'Server error. Is it running? Check logs', type: 'error'}) 
            saveButtons.removeClass('animate btn-success').addClass('btn-warning')
        })
    });
}

function hasOwnProperty(obj, prop) {
    var proto = obj.__proto__ || obj.constructor.prototype;
    return (prop in obj) &&
        (!(prop in proto) || proto[prop] !== obj[prop]);
}

