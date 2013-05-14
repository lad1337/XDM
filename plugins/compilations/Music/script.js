
$(document).ready(function() {
    $('.de-lad1337-music').on('click', '.Album>img', function(){
        var thisImg = this
        var clickedIndex = 0;
        var p = $(this).parent();
        var pp =  p.parent();
        $('.Album',  pp).each(function(i,ele){
            if(ele == p[0])
                clickedIndex = i;
        });
        var musicWidth = 0;
        $('.Music').each(function(i,ele){
            musicWidth += $(this).width();
        })
        
        var rowLength = Math.floor(musicWidth/p.outerWidth(true))
        var row = Math.floor(clickedIndex/rowLength) + 1;
        //console.log('rowlength', rowLength, p.outerWidth(), musicWidth/p.outerWidth())
        
        var lastInRow = $($('.Album', pp)[(rowLength * row) - 1])
        lastInRow.css('padding-bottom', 0)
        
        if(p.hasClass('active')){

            $('.de-lad1337-music .Album').removeClass('active').css('padding-bottom', 0)
            $('.de-lad1337-music .songs').css('height', 0);
            
        }else{
            $('.de-lad1337-music .Album').removeClass('active').css('padding-bottom', 0)
            $('.de-lad1337-music .songs').css('height', 0);
            
            data = {}
            data['id'] = p.data('id')
            jQuery.get( '/getChildrensPaint', data, function(res){
                $('.songs ol',p).html(res)
                
                var colums = 2;
                if($('.de-lad1337-music').width()<598)
                    colums = 1
                
                var neededHeight = Math.round($('ol li', p).length/colums)*20+80;
                if(neededHeight<200)
                    neededHeight = 200
                $('.songs', p).css('height', neededHeight+'px');
                p.css('padding-bottom', (neededHeight)+'px');
                lastInRow.css('padding-bottom', (neededHeight)+'px')
                p.addClass('active');
                rgb = getAverageRGB(thisImg, [0,0,0,1]);
                stringColor = 'rgb('+rgb.r+','+rgb.g+','+rgb.b+')'
                $('.songs', p).css('background', stringColor)
                $('.indi', p).css('color', stringColor)
                //console.log(invertColor(stringColor), brightness(stringColor))
                if(!$('.songs>img' ,p).length){
                    $('.songs' ,p).append('<div class="coverOverlay"></div>')
                    $('.songs' ,p).append($(thisImg).clone())
                    $('.songs .coverOverlay', p).css('box-shadow', 'inset 0 0 14px 9px ' + stringColor);
                }
                if(brightness(stringColor) < 130)
                    $('.songs .bORw', p).css('color', '#fff')
                
                
                
            });
        };
    });
    
    
    
    
    
});

//http://stackoverflow.com/questions/2541481/get-average-color-of-image-via-javascript
function getAverageRGB(imgEl, borderSelect) {
    
    var blockSize = 10, // only visit every 5 pixels
        defaultRGB = {r:0,g:0,b:0}, // for non-supporting envs
        canvas = document.createElement('canvas'),
        context = canvas.getContext && canvas.getContext('2d'),
        data, width, height,
        i = -4,
        length,
        rgb = {r:0,g:0,b:0},
        count = 0,
        borderSize = 0.10; // this is percent
        
    if (!context) {
        return defaultRGB;
    }
    
    height = canvas.height = imgEl.naturalHeight || imgEl.offsetHeight || imgEl.height;
    width = canvas.width = imgEl.naturalWidth || imgEl.offsetWidth || imgEl.width;
    
    context.drawImage(imgEl, 0, 0);
    
    try {
        data = context.getImageData(0, 0, width, height);
    } catch(e) {
        /* security error, img on diff domain */alert('x');
        return defaultRGB;
    }
    
    length = data.data.length;


    var borderOnly = borderSelect[0] + borderSelect[1] + borderSelect[2] + borderSelect[3];
    if(borderOnly){
        var rowLength = width * 4;
        var topBorder = (length * borderSize) * borderSelect[0];
        var bottomBorder = length - length * (borderSize * borderSelect[2]);
        var leftPenetration = borderSize * borderSelect[3];
        var rightPenetration = 1 - (borderSize * borderSelect[1]);
    }
    
    
    while ( (i += blockSize * 4) < length ) {
        if(borderOnly){
            if(i>topBorder && i<=bottomBorder){
                pene = parseFloat('0.'+(i/rowLength).toFixed(2).split('.')[1])
                if(pene > leftPenetration && pene <= rightPenetration){
                    continue;
                }
            }
        }
        
        ++count;
        rgb.r += data.data[i];
        rgb.g += data.data[i+1];
        rgb.b += data.data[i+2];
    }
    
    // ~~ used to floor values
    rgb.r = ~~(rgb.r/count);
    rgb.g = ~~(rgb.g/count);
    rgb.b = ~~(rgb.b/count);
    
    return rgb;
    
}


//http://stackoverflow.com/questions/9101224/invert-text-color-of-a-specific-element-using-jquery
function invertColor(rgb) {
    rgb = [].slice.call(arguments).join(",").replace(/rgb\(|\)|rgba\(|\)|\s/gi, '').split(',');
    for (var i = 0; i < rgb.length; i++) rgb[i] = (i === 3 ? 1 : 255) - rgb[i];
    return 'rgb('+rgb.join(", ")+')';
}

function brightness(rgb){

    rgb = [].slice.call(arguments).join(",").replace(/rgb\(|\)|rgba\(|\)|\s/gi, '').split(',');
    
    
    
    return ((rgb[0] * 299) + (rgb[1] * 587) + (rgb[2] * 114)) / 1000;
    
    
    
}
