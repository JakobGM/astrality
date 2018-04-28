Blockers:
---------

- Change astrality.yml Event listener to Null Island
- Use correct templates folder in compiler.py
- How to handle on_playing in polybar module?
- Initialize module manager with GlobalModulesConfig

Features:
---------

- Add merge option to CSI
- Add option for not expandvars in context/env?
- Still print stdout of running process if TimeOutEx...
- Config option for template file permission bit
- Backup compilation target?
- Index resolution for def 1, 2, 4; getting index 3
- How to insert period specific config? [period/night]? on_specific_period: night: ...action_block...
- Event listeners: season, month
- Arbitrary shell command event
- Watch other paths as a config option
- Add filewatching for context files (can be done with on_modified)
- Local context loading for modules?
- LAST: Change Beta -> Production in setup.py

Documentation:
--------------

- Insert text block documentation
- GNOME startup script
- Add examples of config interpolations in configuration.rst docs
- explain use of colorpicker (gpick)

Example configurations (docs):
------------------------------

- polybar module
- Mouse parallax
- manjaro i3 conky theme?
- Add simple common denominator example to README.rst
- Use Unix configuration survey: https://imgur.com/a/0USMR
- Fix weekday in conky time module

Tests:
------

- Test faulty astrality.yml modification
- Split module tests into separate files
- Add test config file and test interpolations of this file, such as cwd in command substitutions
- Add a test config.yml file which uses both permission types, i.e. 0o777 and '777'

Implementation:
---------------

- Only compile templates explicitly specified, by checking previous period of each module
- Handle references to disabled modules
- Run exit command after confirming validity of astrality.yml
- {module.template_name} replacement with __format__?
- Skip period_change_commands if self.type == static
- Use hash on Resolver to determine if a template needs recompilation.
- Fix all # type: ignore and and force error on missing annotations
- Use timedelta.max in Static timer
- Use dictionaries as return value of RunAction.execute(). Better null object pattern.

Refactoring:
------------

- Cleanup all test names when refactoring and renaming is done

Legalese:
---------

- Ask firewatch for permission
- Find out how to attribute to everything in requirements.in
- Donation? Probably not...

Playground
----------
config/modules:
    enabled_modules:
        - name: global_module
        - name: terminals::iTerm2
        - name: github::jakobgm/color-schemes.astrality::color_schemes
