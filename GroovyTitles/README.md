# GroovyTitles

All config options can be set globally and per channel:
- plugins.groovytitles.bsky.enabled : *true/false*
- plugins.groovytitles.bsky.template : *output template*
- plugins.groovytitles.bsky.timeFormat : *format string for timestamp*
- plugins.groovytitles.youtube.enabled : *true/false*
- plugins.groovytitles.youtube.template : *output template*

Youtube's oembed endpoint is used because it doesn't actively block server IPs or require an API key. The information available from it is limited.

If you're using this alongside SpiffyTitles you may wish to  
```@config plugins.spiffytitles.ignoreddomainpattern /youtube.com|youtu.be/```
