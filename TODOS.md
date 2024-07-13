- [ ] Check for coding style errors
  - [ ] Done within the action itself
- [ ] Build (Make / CMake)
  - [ ] Detect weather it's a Makefile or CMakeFile.txt
  - [ ] Run the corresponding
- [ ] Tests (sh runner, tests/{}.sh)
  - [ ] Agree on a testfile name
  - [ ] Run it within the action
- [ ] Document (doxide, mkdocs)
  - [ ] Run the doxide app
  - [ ] Build the mkdocs.yaml file
  - [ ] Build the html doc using mkdocs
  - [ ] Upload the html doc to the pages repo
- [ ] Additional tools
  - [ ] Agree to a standard in term of additional tools logging (all in tools_logs/{tool_name}/ ?)
  - [ ] Add tools
    - [ ] Integrate gitleaks
- [ ] Integrate with discord
  - [ ] Retreive action logs through discord webhooks
  - [ ] Add the ability (within discord) to run the actions
  - [ ] Add the ability (within discord) to run a "build and release" action (which create a new release, with new v number (x.y.z), cpack compat...)

Final order:

1. Coding style
2. Additional tools (some might also come at != positions)
3. run the "main action (doing all the build and test and document sht)"
4. cleanup
5. if all went good, mirror