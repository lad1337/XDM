

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
    
    $('td.cover a').each(function(){
        var playPaper = new Raphael(this, 100, 77);
        var playIcon1 = playPaper.path(playPathS).attr({fill: "#e6311b", stroke: "none"});
        var playIcon2 = playPaper.path(playPathS2).attr({fill: "#e6311b", stroke: "none"});
        //playIcon.transform('s1.5')
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

function showDownlads(sender, id){
    $(sender).addClass('btn-striped animate');
    var downloadsFrame = $('#downloadsFrame')
    if(!downloadsFrame.length) {
        // set up the bootstrap dialog
        downloadsFrame = $('<div id="fileBrowserDialog" class="modal hide fade"><div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button><h3 id="myModalLabel">Downloads</h3></div><div class="modal-body"></div></div>').appendTo('body')
        downloadsFrame.append('<div class="modal-footer"><button class="btn" data-dismiss="modal">Close</button></div>')
        $('body').append(downloadsFrame)
    }
    
    $('.modal-body', downloadsFrame).empty();
    $.post('/ajaxGetDownloadsFrame', {'id': id}, function(res){
        $('.modal-body', downloadsFrame).html(res)
        downloadsFrame.modal();
        $(sender).removeClass('btn-striped animate');
    })
}

