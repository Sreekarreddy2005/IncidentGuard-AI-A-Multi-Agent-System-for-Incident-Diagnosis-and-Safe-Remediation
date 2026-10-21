.PHONY: all install format lint typecheck test check clean demo serve

all: check

install:
	cd agentops && $(MAKE) install

format:
	cd agentops && $(MAKE) format

lint:
	cd agentops && $(MAKE) lint

typecheck:
	cd agentops && $(MAKE) typecheck

test:
	cd agentops && $(MAKE) test

check:
	cd agentops && $(MAKE) check

clean:
	cd agentops && $(MAKE) clean

demo:
	cd agentops && $(MAKE) demo

serve:
	cd agentops && $(MAKE) serve
