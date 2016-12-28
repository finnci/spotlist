$(document.body).on("click", "#artistSearch", function () {
  $('#mtracklist').empty();
  var art_var;
  art_var = document.getElementById("art_input").value;
  $.ajax({
    type: 'GET',
    url: '/set/search/' + art_var,
    cache: false,
    success: function(response) {
       makeList(response.sets);
      }
  })
});

$(document.body).on("click", "#goplaylist", function () {
  var tracks = $('#mtracklist').children()
  var art_var = document.getElementById("art_input").value;
  var valids = []
  for(var i=0; i<tracks.length; i++) {
    valids[i] = tracks[i].textContent;
  }
  $.ajax({
    type: 'POST',
    url: 'create/playlist/',
    data: JSON.stringify({
      'artist': art_var,
      'songs': valids
    }),
    contentType: 'application/json;',
    success: function(response) {
      $('#mtracklist').empty();
      makeIframe(response.link);
      hideUpload();
    },
    error: function(response) {
      $('#mtracklist').empty();
      var y = response.error;
      makeList(y);
    }
  });
});

function makeIframe(link){
  var list = document.getElementById('mtracklist');
  var item_uno = document.createElement('p');
  item_uno.appendChild(document.createTextNode("Nice.. this playlist is now in your Spotify account"))
  list.appendChild(item_uno);
  var item = document.createElement('p');
  var sp_iframe = document.createElement('iframe');
  sp_iframe.setAttribute("src", link);
  item.className = 'center-inner';
  sp_iframe.className = 'center-inner';
  sp_iframe.style.width=300;
  sp_iframe.style.border='none';
  sp_iframe.style.height=380;
  item.appendChild(sp_iframe);
  list.appendChild(item);
}

function makeList(array){
  var list = document.getElementById('mtracklist');
  for(var i = 0; i < array.length; i++) {
    var item = document.createElement('li');
    item.appendChild(document.createTextNode(array[i]));
    list.appendChild(item);
  }
}

function hideUpload(){
  $("#goplaylist").hide()
}
