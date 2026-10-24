"""Repositories own all database access (TRD §4). Routers and future agent
nodes never issue ad hoc queries — they call application services, which use
these repositories."""
