<h1 id="panoptes-smach-statemachine">PANOPTES Smach StateMachine</h1>

<p><div class="toc"><div class="toc">
<ul>
<li><a href="#panoptes-smach-statemachine">PANOPTES Smach StateMachine</a><ul>
<li><a href="#overview">Overview</a></li>
<li><a href="#panoptes-state-machine">PANOPTES State Machine</a><ul>
<li><a href="#outcomes">Outcomes</a></li>
<li><a href="#state">State</a><ul>
<li><a href="#required-methods">Required Methods</a></li>
<li><a href="#example-state">Example State</a></li>
</ul>
</li>
<li><a href="#statetable">State Table</a><ul>
<li><a href="#panoptes-state-table">PANOPTES State Table</a></li>
</ul>
</li>
<li><a href="#statemachine">State Machine</a></li>
</ul>
</li>
</ul>
</li>
</ul>
</div>
</div>
</p>



<h2 id="overview">Overview</h2>

<p>This document describes how the PANOPTES state machine works, some example uses, as well as instructions for creating additional states or state machines.  The <code>panoptes.statemachine</code>  and <code>panoptes.state</code> classes are both taken directly from the fine work done by the folks over at <a href="http://ros.org">ROS</a> with the <a href="http://wiki.ros.org/smach">smach</a> module they have created. They have many great tutorials and examples. Many of the ideas in this article are presented in the original <a href="http://wiki.ros.org/smach/Documentation">documenation</a> for smach but here they are adapted specifically to PANOPTES.</p>

<p><code>smach</code> defines itself as a “task-level architecture” built upon hierarchical state machines. This means that each state is responsible for executing an arbitrary task and returning an outcome for that state. PANOPTES subclasses the default <code>smach.State</code> to provide a consistent base class for all other states within the project as well as to provide a common interface. </p>

<blockquote>
  <p><strong>Note:</strong> Many features described in the official <a href="http://wiki.ros.org/smach/Documentation">smach documentation</a> are unused by PANOPTES and are hidden by the <code>PanoptesState</code> base class. If you are developing a state and having a hard time making it do something, make sure to check the original documentation and the <code>PanoptesState</code> implementation.</p>
</blockquote>

<h2 id="panoptes-state-machine">PANOPTES State Machine</h2>

<p>State machines are composed of relationships between different states and are based upon an <code>outcome</code> returned by a given state. First we describe the properties of <a href="#outcomes">outcomes</a>, then <a href="#state">states</a>, and finally how a <a href="#statetable">state table</a> is used by the <a href="#statemachine">state machine</a> to tie them all together.</p>



<h3 id="outcomes">Outcomes</h3>

<p>Outcomes are the possible return values from any given state. A state will declare a list of strings in <code>self.outcomes</code> when an instance of the state is created and will set a <code>self.outcome</code> each time the state logic code is run. The <code>outcome</code> set by the state logic must be listed in the defined <code>outcomes</code> for the state. Outcomes have a consistency check done by the state machine before any state is run (see <a href="#statemachine">State Machine</a> below).</p>

<p>Outcomes are always all lowercase strings that correspond to state classes: ‘parking’, ‘slewing’, ‘imaging’, etc.</p>



<h3 id="state">State</h3>

<p>A state class is responsible for declaring potential outcomes and for defining the state logic. Each state should be responsible for one task to be performed, such as scheduling, parking, slewing, etc. </p>

<p>State classes are named in CapWords according to standard <a href="http://legacy.python.org/dev/peps/pep-0008/#class-names">PEP8 conventions</a>. An instance of a state class is named in all caps as per the smach convention (descirbed in the <a href="#statetable">State Table</a> section).</p>



<h4 id="required-methods">Required Methods</h4>

<p>Each state class must implement the <code>setup</code> and <code>run</code> methods:</p>

<dl>
<dt><code>setup</code></dt>
<dd>Called by the <code>__init__</code> method of the base class and responsible for setting the list of possible outcomes via <code>self.outcomes</code> as well as any other initialization required by the state.</dd>

<dt><code>run</code></dt>
<dd>Called by the <code>execute</code> method of the base class and responsible for performing the state logic task and setting the <code>self.outcome</code>.</dd>
</dl>

<blockquote>
  <p><strong>Note:</strong> All states will also have a <code>parking</code> outcome appended to the <code>self.outcomes</code> set by the <code>setup</code> method so that any state can be sent immediately to the <code>Parking</code> state. The base class sets <code>self.outcome</code> to <code>parking</code> by default, so the <code>run</code> method is responsible for changing the outcome as necessary.</p>
</blockquote>



<h4 id="example-state">Example State</h4>



<pre class="prettyprint"><code class="language-python3 hljs python"><span class="hljs-keyword">from</span> panoptes.state <span class="hljs-keyword">import</span> state

<span class="hljs-class"><span class="hljs-keyword">class</span> <span class="hljs-title">Scheduling</span><span class="hljs-params">(state.PanoptesState)</span>:</span>
    <span class="hljs-string">""" 
    A mock Scheduling state. Inherits from common PanoptesState 
    """</span>

    <span class="hljs-function"><span class="hljs-keyword">def</span> <span class="hljs-title">setup</span><span class="hljs-params">(self, *args, **kwargs)</span>:</span>
        <span class="hljs-string">"""
        Called from the __init__ method of the parent class. Has
        access to self.observatory. *args and **kwargs allow passing
        of custom variables.
        """</span>

        <span class="hljs-comment"># Perform any necessary setup</span>
        self.target = self.observatory.get_target()

        <span class="hljs-comment"># Scheduling can only go to slewing (and 'parking')</span>
        self.outcomes=[<span class="hljs-string">'slewing'</span>]

    <span class="hljs-function"><span class="hljs-keyword">def</span> <span class="hljs-title">run</span><span class="hljs-params">(self)</span>:</span>
        <span class="hljs-string">"""
        Called once per state and is responsible for the state 
        logic (the task to be performed). Here some dummy 
        logic code gets the coordinates for the next target and 
        assigns them to the observatory.
        """</span>
        <span class="hljs-keyword">try</span>:
            <span class="hljs-comment"># Perform the state logic</span>
            self.observatory.mount.set_target_coordinates(self.target)

            <span class="hljs-comment"># Set the successful outcome based on state logic</span>
            self.outcome = <span class="hljs-string">'slewing'</span>
        <span class="hljs-keyword">except</span>:
            <span class="hljs-comment"># If state logic fails, outcome will is 'parking'</span>
            self.logger.warning(<span class="hljs-string">"Scheduling failed"</span>)</code></pre>

<h3 id="statetable">State Table</h3>

<p>A state table is essentially just a “plan” for the PANOPTES unit to follow.  State tables are stored in yaml files within the <code>$ROOT_DIR/panoptes/state_tables</code> directory and are used by setting the <code>state_machine</code> config key to the corresponding name of the file (without the .yaml).</p>

<p>Each state has a set of possible outcomes that will become the outcome:state transitions. The ordering of the outcomes does not matter. State instances are named in all UPPERCASE while outcomes are always lowercase.</p>



<h4 id="panoptes-state-table">PANOPTES State Table</h4>

<p>This is the current state table plan for PANOPTES corresponding to the image below. Here we see that there will be an instance of the Parking class created called PARKING that has three possible outcomes: ‘shutdown’, ‘ready’, and ‘quit’. The ‘quit’ state is a special outcome that will stop execution of the state machine, otherwise the PANOPTES state machine is set to loop indefinitely (‘sleeping’ in the day).</p>



<pre class="prettyprint"><code class="language-yaml hljs haml"><span class="hljs-tag">%</span> panoptes_state_table.yaml
-<span class="ruby">--
</span>PARKED:
 -<span class="ruby"> shutdown
</span> -<span class="ruby"> ready
</span> -<span class="ruby"> quit
</span>PARKING:
 -<span class="ruby"> parked
</span>SHUTDOWN:
 -<span class="ruby"> sleeping
</span>SLEEPING:
 -<span class="ruby"> ready
</span>READY:
 -<span class="ruby"> scheduling
</span>SCHEDULING:
 -<span class="ruby"> slewing
</span>SLEWING:
 -<span class="ruby"> imaging
</span> -<span class="ruby"> test_imaging
</span>IMAGING:
 -<span class="ruby"> analyzing
</span>ANALYZING:
 -<span class="ruby"> slewing
</span> -<span class="ruby"> scheduling
</span>TEST_IMAGING:
 -<span class="ruby"> analyzing</span></code></pre>

<p><img src="https://camo.githubusercontent.com/b6d558141fbad5fc28ab2029742fae0ce8fa7ead/687474703a2f2f70726f6a65637470616e6f707465732e6f72672f76312f77702d636f6e74656e742f75706c6f6164732f323031332f31312f504f43532e706e67" alt="PANOPTES State Diagram" title=""></p>

<blockquote>
  <p><strong>Note:</strong> The ‘quit’ outcome is not depicted in the above image</p>
</blockquote>



<h3 id="statemachine">State Machine</h3>

<p>The state machine itself merely creates instances of the states (based on the keys in the state table file) and adds them to the state machine. A consistency check is performed automatically by the state machine to make sure that all possible outcomes for a state are known outcomes and that a valid path through the state machine actually exists.</p>

<p>State machines themselves can be viewed as individual states and thus nested. For instance, the PANOPTES state machine itself only has one possible outcome - quit - which normally causes the state machine to be terminated. However, if you treat the entire state machine as one state, you can embed it within a larger state machine that would then map out a transition between the ‘quit’ outcome and a different state.</p>

<p>Or, for example, if we decide that the Imaging state is better defined as a VisitTarget state, we can in turn make the Visit state be a mini state machine in itself, composed of various sub states (Imaging, Analyzing, TestImaging). This Visit state would then return an outcome, which would happily be used by the larger PANOPTES state machine.</p>

<p>For more information on how states can be nested (hierarchical state machines) within each other refer to the smach <a href="http://wiki.ros.org/smach/Tutorials/Create%20a%20hierarchical%20state%20machine">tutorial on HSMs</a></p>

<blockquote>
  <p>Written by <a href="https://github.com/wtgee">wtgee</a>.</p>
</blockquote>