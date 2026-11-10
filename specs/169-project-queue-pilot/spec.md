# Feature: Manual project queue pilot

An OpenBenches maintainer can prepare a two- or three-PR same-repo stack that
touches only the checkout wrapper and its fixture suite. Each approved head
passes focused fast checks; one combined run must pass on both supported
platforms before the stack is eligible to land. Stale approvals or mixed paths
fail closed. The config PR demonstrates platform coverage without queuing.
