PS D:\projects\dc-bot\fetch> docker-compose logs -f
discord-bot-1  | 2026-03-03 17:33:18,212 [INFO] Discord Daily Tech Bot — starting up
discord-bot-1  | 2026-03-03 17:33:18,212 [INFO] ✅ All env vars present: DISCORD_WEBHOOK_URL, OPENROUTER_API_KEY, X_USERNAME, X_PASSWORD, X_EMAIL, X_EMAIL_PW
discord-bot-1  | 2026-03-03 17:33:18.217 | INFO     | twscrape.db:migrate:96 - Running migration to v1
discord-bot-1  | 2026-03-03 17:33:18.256 | INFO     | twscrape.db:migrate:96 - Running migration to v2
discord-bot-1  | 2026-03-03 17:33:18.291 | INFO     | twscrape.db:migrate:96 - Running migration to v3
discord-bot-1  | 2026-03-03 17:33:18.313 | INFO     | twscrape.db:migrate:96 - Running migration to v4
discord-bot-1  | 2026-03-03 17:33:18,337 [INFO] twscrape: no accounts — adding account and logging in…
discord-bot-1  | 2026-03-03 17:33:18.395 | INFO     | twscrape.accounts_pool:add_account:110 - Account Wed1864569 added successfully (active=False)     
discord-bot-1  | 2026-03-03 17:33:18.400 | INFO     | twscrape.accounts_pool:login_all:183 - [1/1] Logging in Wed1864569 - w12401804@gmail.com
discord-bot-1  | 2026-03-03 17:33:18,625 [INFO] HTTP Request: POST https://api.x.com/1.1/guest/activate.json "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:18,634 [INFO] HTTP Request: POST https://api.x.com/1.1/onboarding/task.json?flow_name=login "HTTP/1.1 403 Forbidden"  
discord-bot-1  | 2026-03-03 17:33:18.635 | ERROR    | twscrape.accounts_pool:login:162 - Failed to login 'Wed1864569': 403 - <!DOCTYPE html>
discord-bot-1  | <!--[if lt IE 7]> <html class="no-js ie6 oldie" lang="en-US"> <![endif]-->
discord-bot-1  | <!--[if IE 7]>    <html class="no-js ie7 oldie" lang="en-US"> <![endif]-->
discord-bot-1  | <!--[if IE 8]>    <html class="no-js ie8 oldie" lang="en-US"> <![endif]-->
discord-bot-1  | <!--[if gt IE 8]><!--> <html class="no-js" lang="en-US"> <!--<![endif]-->
discord-bot-1  | <head>
discord-bot-1  | <title>Attention Required! | Cloudflare</title>
discord-bot-1  | <meta charset="UTF-8" />
discord-bot-1  | <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
discord-bot-1  | <meta http-equiv="X-UA-Compatible" content="IE=Edge" />    
discord-bot-1  | <meta name="robots" content="noindex, nofollow" />
discord-bot-1  | <meta name="viewport" content="width=device-width,initial-scale=1" />
discord-bot-1  | <link rel="stylesheet" id="cf_styles-css" href="/cdn-cgi/styles/cf.errors.css" />
discord-bot-1  | <!--[if lt IE 9]><link rel="stylesheet" id='cf_styles-ie-css' href="/cdn-cgi/styles/cf.errors.ie.css" /><![endif]-->
discord-bot-1  | <style>body{margin:0;padding:0}</style>
discord-bot-1  |
discord-bot-1  |
discord-bot-1  | <!--[if gte IE 10]><!-->
discord-bot-1  | <script>
discord-bot-1  |   if (!navigator.cookieEnabled) {
discord-bot-1  |     window.addEventListener('DOMContentLoaded', function () {
discord-bot-1  |       var cookieEl = document.getElementById('cookie-alert');
discord-bot-1  |       cookieEl.style.display = 'block';
discord-bot-1  |     })
discord-bot-1  |   }
discord-bot-1  | </script>
discord-bot-1  | <!--<![endif]-->
discord-bot-1  |
discord-bot-1  | </head>
discord-bot-1  | <body>
discord-bot-1  |   <div id="cf-wrapper">
discord-bot-1  |     <div class="cf-alert cf-alert-error cf-cookie-error" id="cookie-alert" data-translate="enable_cookies">Please enable cookies.</div>
discord-bot-1  |     <div id="cf-error-details" class="cf-error-details-wrapper">
discord-bot-1  |       <div class="cf-wrapper cf-header cf-error-overview"> 
discord-bot-1  |         <h1 data-translate="block_headline">Sorry, you have been blocked</h1>
discord-bot-1  |         <h2 class="cf-subheadline"><span data-translate="unable_to_access">You are unable to access</span> x.com</h2>
discord-bot-1  |       </div><!-- /.header -->
discord-bot-1  |
discord-bot-1  |       <div class="cf-section cf-highlight">
discord-bot-1  |         <div class="cf-wrapper">
discord-bot-1  |           <div class="cf-screenshot-container cf-screenshot-full">
discord-bot-1  |
discord-bot-1  |               <span class="cf-no-screenshot error"></span> 
discord-bot-1  |
discord-bot-1  |           </div>
discord-bot-1  |         </div>
discord-bot-1  |       </div><!-- /.captcha-container -->
discord-bot-1  |
discord-bot-1  |       <div class="cf-section cf-wrapper">
discord-bot-1  |         <div class="cf-columns two">
discord-bot-1  |           <div class="cf-column">
discord-bot-1  |             <h2 data-translate="blocked_why_headline">Why have I been blocked?</h2>
discord-bot-1  |
discord-bot-1  |             <p data-translate="blocked_why_detail">This website is using a security service to protect itself from online attacks. The action you just performed triggered the security solution. There are several actions that could trigger this block including submitting a certain word or phrase, a SQL command or malformed data.</p>
discord-bot-1  |           </div>
discord-bot-1  |
discord-bot-1  |           <div class="cf-column">
discord-bot-1  |             <h2 data-translate="blocked_resolve_headline">What can I do to resolve this?</h2>
discord-bot-1  |
discord-bot-1  |             <p data-translate="blocked_resolve_detail">You can email the site owner to let them know you were blocked. Please include what you were doing when this page came up and the Cloudflare Ray ID found at the bottom of this page.</p>
discord-bot-1  |           </div>
discord-bot-1  |         </div>
discord-bot-1  |       </div><!-- /.section -->
discord-bot-1  |
discord-bot-1  |       <div class="cf-error-footer cf-wrapper w-240 lg:w-full py-10 sm:py-4 sm:px-8 mx-auto text-center sm:text-left border-solid border-0 border-t border-gray-300">
discord-bot-1  |     <p class="text-13">
discord-bot-1  |       <span class="cf-footer-item sm:block sm:mb-1">Cloudflare Ray ID: <strong class="font-semibold">9d6a62af0a47f51a</strong></span>  
discord-bot-1  |       <span class="cf-footer-separator sm:hidden">&bull;</span>
discord-bot-1  |       <span id="cf-footer-item-ip" class="cf-footer-item hidden sm:block sm:mb-1">
discord-bot-1  |         Your IP:
discord-bot-1  |         <button type="button" id="cf-footer-ip-reveal" class="cf-footer-ip-reveal-btn">Click to reveal</button>
discord-bot-1  |         <span class="hidden" id="cf-footer-ip">123.202.171.80</span>
discord-bot-1  |         <span class="cf-footer-separator sm:hidden">&bull;</span>
discord-bot-1  |       </span>
discord-bot-1  |       <span class="cf-footer-item sm:block sm:mb-1"><span>Performance &amp; security by</span> <a rel="noopener noreferrer" href="https://www.cloudflare.com/5xx-error-landing" id="brand_link" target="_blank">Cloudflare</a></span>
discord-bot-1  |
discord-bot-1  |     </p>
discord-bot-1  |     <script>(function(){function d(){var b=a.getElementById("cf-footer-item-ip"),c=a.getElementById("cf-footer-ip-reveal");b&&"classList"in b&&(b.classList.remove("hidden"),c.addEventListener("click",function(){c.classList.add("hidden");a.getElementById("cf-footer-ip").classList.remove("hidden")}))}var a=document;document.addEventListener&&a.addEventListener("DOMContentLoaded",d)})();</script>
discord-bot-1  |   </div><!-- /.error-footer -->
discord-bot-1  |
discord-bot-1  |     </div><!-- /#cf-error-details -->
discord-bot-1  |   </div><!-- /#cf-wrapper -->
discord-bot-1  |
discord-bot-1  |   <script>
discord-bot-1  |     window._cf_translation = {};
discord-bot-1  |
discord-bot-1  |
discord-bot-1  |   </script>
discord-bot-1  | </body>
discord-bot-1  | </html>
discord-bot-1  | 2026-03-03 17:33:18,662 [INFO] ✅ twscrape login complete  
discord-bot-1  | 2026-03-03 17:33:18,662 [INFO] ═══ Daily job started at 2026-03-04 01:33:18 HKT ═══
discord-bot-1  | 2026-03-03 17:33:18,667 [INFO] Fetching 11 RSS feeds concurrently…
discord-bot-1  | 2026-03-03 17:33:18,698 [INFO] HTTP Request: GET https://hackaday.com/blog/feed/ "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:18,721 [INFO] RSS [hackaday]: 5 entries   
discord-bot-1  | 2026-03-03 17:33:19,029 [INFO] HTTP Request: GET https://www.hackster.io/feed "HTTP/1.1 302 Found"
discord-bot-1  | 2026-03-03 17:33:19,365 [INFO] HTTP Request: GET https://www.thingiverse.com/rss "HTTP/1.1 404 Not Found"
discord-bot-1  | 2026-03-03 17:33:19,370 [WARNING] RSS fetch failed [thingiverse] https://www.thingiverse.com/rss: Client error '404 Not Found' for url 'https://www.thingiverse.com/rss'
discord-bot-1  | For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
discord-bot-1  | 2026-03-03 17:33:19,540 [INFO] HTTP Request: GET https://www.printables.com/rss.xml "HTTP/1.1 404 Not Found"
discord-bot-1  | 2026-03-03 17:33:19,541 [WARNING] RSS fetch failed [printables] https://www.printables.com/rss.xml: Client error '404 Not Found' for url 'https://www.printables.com/rss.xml'
discord-bot-1  | For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
discord-bot-1  | 2026-03-03 17:33:19,644 [INFO] HTTP Request: GET https://www.reddit.com/r/maker/.rss "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:19,698 [INFO] HTTP Request: GET https://www.hackster.io/users/sign_in?redirect_to=%2Ffeed "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:19,714 [WARNING] RSS bozo flag [hackster]: <unknown>:58:44: not well-formed (invalid token)
discord-bot-1  | 2026-03-03 17:33:19,715 [INFO] RSS [hackster]: 0 entries   
discord-bot-1  | 2026-03-03 17:33:19,717 [INFO] HTTP Request: GET https://www.reddit.com/r/3Dprinting/.rss "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:19,724 [INFO] HTTP Request: GET https://www.reddit.com/r/RP2040/.rss "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:19,878 [INFO] RSS [reddit_maker]: 5 entries
discord-bot-1  | 2026-03-03 17:33:19,879 [INFO] HTTP Request: GET https://www.reddit.com/r/arduino/.rss "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:19,954 [INFO] RSS [reddit_rp2040]: 3 entries
discord-bot-1  | 2026-03-03 17:33:20,002 [INFO] HTTP Request: GET https://www.reddit.com/r/esp32/.rss "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:20,162 [INFO] RSS [reddit_3dprinting]: 5 entries
discord-bot-1  | 2026-03-03 17:33:20,258 [INFO] RSS [reddit_esp32]: 5 entries
discord-bot-1  | 2026-03-03 17:33:20,339 [INFO] RSS [reddit_arduino]: 5 entries
discord-bot-1  | 2026-03-03 17:33:21,072 [INFO] HTTP Request: GET https://blog.adafruit.com/feed/ "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:21,349 [INFO] RSS [adafruit]: 5 entries
discord-bot-1  | 2026-03-03 17:33:21,903 [INFO] HTTP Request: GET https://hnrss.org/newest?q=AI+LLM&points=10 "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:21,909 [INFO] RSS [hn_ai]: 3 entries
discord-bot-1  | 2026-03-03 17:33:21.927 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:21.943 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:21,943 [INFO] AI: primary → 0 tweets; retry with min_faves=5
discord-bot-1  | 2026-03-03 17:33:21.957 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:21.971 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:21,971 [INFO] AI: 0 tweets from X
discord-bot-1  | 2026-03-03 17:33:21,971 [INFO] AI: 3 RSS + 0 X → 3 merged  
discord-bot-1  | 2026-03-03 17:33:23,743 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:26,840 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for AI: 'NoneType' object has no attribute 'strip'    
discord-bot-1  | 2026-03-03 17:33:27,442 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:31,847 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → AI: 335 chars
discord-bot-1  | 2026-03-03 17:33:33.862 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:33.875 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:33,875 [INFO] ESP32: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:33:33.892 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:33.908 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:33,908 [INFO] ESP32: 0 tweets from X      
discord-bot-1  | 2026-03-03 17:33:33,908 [INFO] ESP32: 5 RSS + 0 X → 5 merged
discord-bot-1  | 2026-03-03 17:33:34,805 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:37,391 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for ESP32: 'NoneType' object has no attribute 'strip' 
discord-bot-1  | 2026-03-03 17:33:38,301 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:50,386 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → ESP32: 651 chars
discord-bot-1  | 2026-03-03 17:33:52.403 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:52.417 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:52,417 [INFO] RP2040: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:33:52.433 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:52.450 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:33:52,450 [INFO] RP2040: 0 tweets from X     
discord-bot-1  | 2026-03-03 17:33:52,450 [INFO] RP2040: 3 RSS + 0 X → 3 merged
discord-bot-1  | 2026-03-03 17:33:54,110 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:33:56,742 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for RP2040: 'NoneType' object has no attribute 'strip'
discord-bot-1  | 2026-03-03 17:33:57,642 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:34:21,741 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → RP2040: 467 chars
discord-bot-1  | 2026-03-03 17:34:23.760 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:23.777 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:23,777 [INFO] RP2350: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:34:23.792 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:23,805 [INFO] RP2350: 0 tweets from X
discord-bot-1  | 2026-03-03 17:34:23,805 [INFO] RP2350: 0 RSS + 0 X → 0 merged
discord-bot-1  | 2026-03-03 17:34:23.805 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:23,806 [WARNING] RP2350: fewer than 3 posts available
discord-bot-1  | 2026-03-03 17:34:25.824 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:25.836 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:25,837 [INFO] Arduino: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:34:25.853 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:25.868 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:25,868 [INFO] Arduino: 0 tweets from X    
discord-bot-1  | 2026-03-03 17:34:25,868 [INFO] Arduino: 5 RSS + 0 X → 5 merged
discord-bot-1  | 2026-03-03 17:34:26,825 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:34:29,439 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for Arduino: 'NoneType' object has no attribute 'strip'
discord-bot-1  | 2026-03-03 17:34:30,066 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:34:38,589 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → Arduino: 394 chars
discord-bot-1  | 2026-03-03 17:34:40.581 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:40.594 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:40,594 [INFO] Maker: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:34:40.608 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:40.622 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:34:40,622 [INFO] Maker: 0 tweets from X      
discord-bot-1  | 2026-03-03 17:34:40,622 [INFO] Maker: 11 RSS + 0 X → 11 merged
discord-bot-1  | 2026-03-03 17:34:42,074 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:34:44,934 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for Maker: 'NoneType' object has no attribute 'strip' 
discord-bot-1  | 2026-03-03 17:34:45,520 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:35:18,458 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → Maker: 593 chars
discord-bot-1  | 2026-03-03 17:35:20.483 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:35:20.503 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:35:20,503 [INFO] 3D列印: primary → 0 tweets; retry with min_faves=1
discord-bot-1  | 2026-03-03 17:35:20.523 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:35:20.540 | WARNING  | twscrape.accounts_pool:get_for_queue_or_wait:297 - No active accounts. Stopping...
discord-bot-1  | 2026-03-03 17:35:20,540 [INFO] 3D列印: 0 tweets from X     
discord-bot-1  | 2026-03-03 17:35:20,540 [INFO] 3D列印: 5 RSS + 0 X → 5 merged
discord-bot-1  | 2026-03-03 17:35:21,761 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:35:24,547 [WARNING] OpenRouter [stepfun/step-3.5-flash:free] error for 3D列印: 'NoneType' object has no attribute 'strip'
discord-bot-1  | 2026-03-03 17:35:25,103 [INFO] HTTP Request: POST https://openrouter.ai/api/v1/chat/completions "HTTP/1.1 200 OK"
discord-bot-1  | 2026-03-03 17:35:33,905 [INFO] ✅ AI [arcee-ai/trinity-large-preview:free] → 3D列印: 418 chars
discord-bot-1  | 2026-03-03 17:35:36,372 [INFO] HTTP Request: POST https://discordapp.com/api/webhooks/1478442946108985435/x-qXc732vYwp9LjIiSoIIuEdRpSvMcEcOj2HEpFD-UZZ2iKQ_2gGvrcZD_eDCvWuMcNk "HTTP/1.1 204 No Content"
discord-bot-1  | 2026-03-03 17:35:36,373 [INFO] ✅ Discord webhook delivered (7 embeds, HTTP 204)
discord-bot-1  | 2026-03-03 17:35:36,373 [INFO] ═══ Daily job complete in 137.8s ═══
discord-bot-1  | 2026-03-03 17:35:36,375 [INFO] Adding job tentatively -- it will be properly scheduled when the scheduler starts
discord-bot-1  | 2026-03-03 17:35:36,375 [INFO] Added job "main.<locals>._job" to job store "default"
discord-bot-1  | 2026-03-03 17:35:36,376 [INFO] Scheduler started
discord-bot-1  | 2026-03-03 17:35:36,376 [INFO] ⏰ Next scheduled run: 2026-03-04 13:30:00+08:00