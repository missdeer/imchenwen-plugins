
var website_name = 'Youtube';

var website_description = '\
    <p>Welcome to Youtube!<p>\
    <p>\
        Before using, you need to\
        <a href="plugin:set-api-key">set Youtube API Key</a>\
        first.\
    </p>\
    <p>\
        <a href="https://www.slickremix.com/docs/get-api-key-for-youtube/">How to get the API Key?</a>\
    </p>'

    
var api_key = imchenwen.get_configuration('api_key');
var pageTokens = [];


function serialize(obj) {
  var str = [];
  for(var p in obj)
     str.push(encodeURIComponent(p) + "=" + encodeURIComponent(obj[p]));
  return str.join("&");
}


// Search
function search(key, page) {
    if (key === 'plugin:set-api-key') {
        set_api_key();
        return;
    }

    if (api_key === undefined) {
        imchenwen.warning('Please set the API key first!');
        return;
    }

    var qs = {
        'q': key,
        'maxResults': 25,
        'safeSearch': 'none',
        'part': 'id,snippet',
        'type': 'video',
        'key': api_key
    };
    if (page === 1)
        pageTokens = ['', ''];
    else if (page < pageTokens.length)
        qs['pageToken'] = pageTokens[page];
    else {
        imchenwen.warning("Cannot skip page due to the limitation of Youtube's API.");
        return;
    }
    var url = 'https://www.googleapis.com/youtube/v3/search?' + serialize(qs);
    imchenwen.get_content(url, function(content) {
        var data = JSON.parse(content);
        var result = [];
        for (var i in data.items) {
            var item = data.items[i];
            var t = {
                title: item.snippet.title,
                url: 'https://www.youtube.com/watch?v=' + item.id.videoId
            };
            result.push(t);
        }
        if (page + 1 === pageTokens.length && 'nextPageToken' in data)
            pageTokens.push(data.nextPageToken);
        imchenwen.show_result(result);
    });
}

// Set API key
function set_api_key() {
    imchenwen.get_text('Please enter a new API Key:', api_key, function(text) {
        api_key = text;
        imchenwen.set_configuration('api_key', api_key);
        imchenwen.information('Successfully set the API Key.');
    });
}
