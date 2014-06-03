<h2 id="pocs-config">POCS Config</h2>

<p>This will be a quick tutorial on how to use the POCS configuration files. There is a global config file that comes with the project and then a local config file which the developer can create to add/edit config settings.</p>

<p>We are going to dive right into using the config and then talk about some of the details after.</p>

<p>First, let’s take a look at part of <code>config.yaml</code> so you know what we are dealing with:</p>

<pre class="prettyprint prettyprinted"><code><span class="pun">%</span><span class="pln"> </span><span class="typ">Global</span><span class="pln"> </span><span class="typ">Configuration</span><span class="pln"> </span><span class="typ">File</span><span class="pln">
</span><span class="pun">---</span><span class="pln">
name</span><span class="pun">:</span><span class="pln"> </span><span class="str">'Panoptes Base #1'</span><span class="pln">
site</span><span class="pun">:</span><span class="pln"> </span><span class="com"># Mauna Loa Observatory</span><span class="pln">
    lat</span><span class="pun">:</span><span class="pln"> </span><span class="str">'19:32:09.3876'</span><span class="pln">
    lon</span><span class="pun">:</span><span class="pln"> </span><span class="str">'-155:34:34.3164'</span><span class="pln">
    elevation</span><span class="pun">:</span><span class="pln"> </span><span class="lit">3400.0</span><span class="pln">
    horizon</span><span class="pun">:</span><span class="pln"> </span><span class="pun">-</span><span class="lit">12.0</span><span class="pln">
mount</span><span class="pun">:</span><span class="pln">
    model</span><span class="pun">:</span><span class="pln"> ioptron
    port</span><span class="pun">:</span><span class="pln"> </span><span class="str">'/dev/ttyUSB0'</span><span class="pln">
log_dir</span><span class="pun">:</span><span class="pln"> </span><span class="str">'/var/log/Panoptes/'</span><span class="pln">
log_file</span><span class="pun">:</span><span class="pln"> panoptes</span><span class="pun">.</span><span class="pln">log</span></code></pre>

<p>Pretty simple. There shouldn’t be anything surprising in there. The YAML ‘document’ begins with the <code>---</code> and everything above is meta-data about the file while that below is what you will have access to.  Strings can be wrapped in quotes but don’t need to be.</p>

<h3 id="usage">Usage</h3>

<p>The <code>panoptes.utils.config</code> decorator takes care of reading in the configuration files by first reading <code>config.yaml</code>, then checking for <code>config_local.yaml</code> and using that to replace any values loaded from the global config. All values can be overriden and <strong>not all options are currently documented in <code>config.yaml</code></strong>.</p>

<p>To use something from the config, make sure the class is decorated:</p>

<pre class="prettyprint prettyprinted"><code><span class="kwd">import</span><span class="pln"> panoptes</span><span class="pun">.</span><span class="pln">utils</span><span class="pun">.</span><span class="pln">logger </span><span class="kwd">as</span><span class="pln"> logger
</span><span class="kwd">import</span><span class="pln"> panoptes</span><span class="pun">.</span><span class="pln">utils</span><span class="pun">.</span><span class="pln">config </span><span class="kwd">as</span><span class="pln"> config

</span><span class="lit">@logger</span><span class="pun">.</span><span class="pln">has_logger
</span><span class="lit">@config</span><span class="pun">.</span><span class="pln">has_config
</span><span class="kwd">class</span><span class="pln"> </span><span class="typ">Mount</span><span class="pun">():</span><span class="pln">
    </span><span class="kwd">def</span><span class="pln"> __init__</span><span class="pun">(</span><span class="kwd">self</span><span class="pun">):</span><span class="pln">
        mount_config </span><span class="pun">=</span><span class="pln"> </span><span class="kwd">self</span><span class="pun">.</span><span class="pln">config</span><span class="pun">.</span><span class="kwd">get</span><span class="pun">(</span><span class="str">'mount'</span><span class="pun">)</span><span class="pln">
        </span><span class="kwd">assert</span><span class="pln"> mount_config </span><span class="kwd">is</span><span class="pln"> </span><span class="kwd">not</span><span class="pln"> </span><span class="kwd">None</span><span class="pln">

        port </span><span class="pun">=</span><span class="pln"> mount_config</span><span class="pun">.</span><span class="kwd">get</span><span class="pun">(</span><span class="str">'port'</span><span class="pun">,</span><span class="pln"> </span><span class="str">'/dev/ttyUSB0'</span><span class="pun">)</span><span class="pln">
        </span><span class="kwd">self</span><span class="pun">.</span><span class="pln">logger</span><span class="pun">.</span><span class="pln">info</span><span class="pun">(</span><span class="str">'Mount is using port: {}'</span><span class="pun">.</span><span class="pln">format</span><span class="pun">(</span><span class="pln">port</span><span class="pun">))</span></code></pre>

<p>A couple of things are going on here:</p>

<ul>
<li><code>self.config</code> is automatically available to the class (it has been ‘decorated’) and is a python <code>dict()</code> object, corresponding to the YAML.</li>
<li><code>self.config</code> contains <em>all</em> the configuration items.</li>
<li><code>mount_config</code> is also a <code>dict()</code> object so you can still use the standard python <code>dict()</code> methods.  <a href="#dict-methods">See below</a> for details.</li>
<li><code>mount_config.get('port', '/dev/ttyUSB0')</code> will return either the <code>port</code> config item, or a default of <code>/dev/ttyUSB0</code>. Again, <a href="#dict-methods">see below</a> for details.</li>
</ul>

<p>That’s really all there is to it. That should allow you to start putting items in the config files and using them within the code. Below are details and more information.</p>

<hr>



<h3 id="config-files">Config Files</h3>

<p>There are two configuration files for the project that reside in the project’s root directory. </p>

<dl>
<dt><code>config.yaml</code></dt>
<dd>The global configuration file. This file is contained within the repository and contains the default global settings. 

<blockquote>
  <strong>Note:</strong> This file should not be edited
</blockquote></dd>

<dt><code>config_local.yaml</code></dt>
<dd>The local configuration file. This file supercedes the the entries in the main config file, so if you want to replace or add configuration items, do it in this file. 

<blockquote>
  <strong>Note:</strong> This file does not exist in the repository so it is up to the user to create
</blockquote></dd>
</dl>

<h3 id="config-structure-yaml">Config Structure: YAML</h3>

<p>The config files are done in <a href="http://www.yaml.org/">YAML</a>, which is a standard way to serialize objects.<a href="#fn:json" id="fnref:json" title="See footnote" class="footnote">1</a>  Basically, this allows for turning data structures (lists, arrays, dicts, scalars) into a string and saving them to a file and then later reading that file back in and automatically having the data structures available to you. The nice thing is that it is so standard that you can use any language/platform to read/write YAML files, so it is essentially a way to save and move data bewteen programs.</p>

<p>YAML is simple to use with <a href="http://pyyaml.org/wiki/PyYAMLDocumentation">PyYAML</a>:</p>

<blockquote>
  <p><strong>Note</strong> The <code>Config</code> class decorator takes care of all of this for configuration. This is just for educational purposes. To see how <code>Config</code> is actually implemented, check the <a href="https://github.com/panoptes/POCS/blob/develop/panoptes/utils/config.py">source</a>.</p>
</blockquote>



<pre class="prettyprint prettyprinted"><code><span class="kwd">import</span><span class="pln"> yaml

</span><span class="com"># Two config files</span><span class="pln">
global_config </span><span class="pun">=</span><span class="pln"> </span><span class="str">'config.yaml'</span><span class="pln">
local_config </span><span class="pun">=</span><span class="pln"> </span><span class="str">'config_local.yaml'</span><span class="pln">

</span><span class="com"># Create empty config</span><span class="pln">
config </span><span class="pun">=</span><span class="pln"> dict</span><span class="pun">()</span><span class="pln">

</span><span class="com"># Read in global config and update dict()</span><span class="pln">
</span><span class="kwd">with</span><span class="pln"> open</span><span class="pun">(</span><span class="pln">global_config</span><span class="pun">,</span><span class="pln"> </span><span class="str">'r'</span><span class="pun">)</span><span class="pln"> </span><span class="kwd">as</span><span class="pln"> f</span><span class="pun">:</span><span class="pln">
    global_items </span><span class="pun">=</span><span class="pln"> yaml</span><span class="pun">.</span><span class="pln">load</span><span class="pun">(</span><span class="pln">f</span><span class="pun">.</span><span class="pln">read</span><span class="pun">())</span><span class="pln">
    config</span><span class="pun">.</span><span class="pln">update</span><span class="pun">(</span><span class="pln">global_items</span><span class="pun">)</span><span class="pln">

</span><span class="com"># Do the same thing with local, updating same dict()</span><span class="pln">
</span><span class="kwd">with</span><span class="pln"> open</span><span class="pun">(</span><span class="pln">local_config</span><span class="pun">,</span><span class="pln"> </span><span class="str">'r'</span><span class="pun">)</span><span class="pln"> </span><span class="kwd">as</span><span class="pln"> f</span><span class="pun">:</span><span class="pln">
    local_items </span><span class="pun">=</span><span class="pln"> yaml</span><span class="pun">.</span><span class="pln">load</span><span class="pun">(</span><span class="pln">f</span><span class="pun">.</span><span class="pln">read</span><span class="pun">())</span><span class="pln">
    config</span><span class="pun">.</span><span class="pln">update</span><span class="pun">(</span><span class="pln">local_items</span><span class="pun">)</span></code></pre>

<p>You can see that it’s pretty simple. <code>yaml.load</code> and <code>yaml.dump</code> are the work-horses of PyYAML. Check the <a href="http://pyyaml.org/wiki/PyYAMLDocumentation">docs</a> for details.</p>

<h3 id="dict-methods">Python dict() methods</h3>

<p>Python has a number of built in methods for <code>dict()</code> objects documented <a href="https://docs.python.org/3.4/library/stdtypes.html#mapping-types-dict">here</a>. I prefer to use the following:</p>

<dl>
<dt><code>self.config.get(key, [default])</code></dt>
<dd>This will look for the <code>key</code> given and return the value (which can be another data structure) or <code>None</code>. If <code>default</code> is provided, will return <code>default</code> instead of <code>None</code>.</dd>

<dt><code>self.config.setdefault(key, [default])</code></dt>
<dd>Same as <code>.get()</code>, but if <code>default</code> is provided, this will update <code>self.config</code>, setting the the <code>key</code> to <code>default</code> and then returning <code>default</code>. If <code>key</code> already exists, <code>default</code> is ignored and <code>self.config</code> is not updated

<blockquote>
  <strong>Note</strong> <code>.setdefault()</code> updates <code>self.config</code> in memory, it does not update the actual configuration file.
</blockquote></dd>

<dt><code>self.config.update(dict)</code></dt>
<dd>This accepts a <code>dict()</code> object and updates <code>self.config</code> with any matching key/value pairs. <code>key</code>s not in <code>self.config</code> will be added and existing ones will be replaced.</dd>
</dl>

<hr>

<blockquote>
  <p>Written by <a href="https://github.com/wtgee">@wtgee</a></p>
</blockquote><div class="footnotes"><hr><ol><li id="fn:json"><a href="http://www.json.org/">JSON</a> is similar and just as pervasive. Because YAML tends to be more human-readable (in addition to machine-readable), it is often used for things like config files. Because JSON tends to be more efficient (whitespace/size), it tends to be more used between machines. Most web data is exchanged via JSON these days. <a href="#fnref:json" title="Return to article" class="reversefootnote">↩</a></li></ol></div>