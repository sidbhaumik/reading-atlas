---
title: CAP theorem
tags: [systems]
source: https://en.wikipedia.org/wiki/CAP_theorem
---

# CAP theorem

In database theory, the CAP theorem, also named Brewer's theorem after computer scientist Eric Brewer, states that any distributed data store can provide at most two of the following three guarantees:ConsistencyEvery read receives the most recent write or an error. Consistency means that all clients see the same data at the same time, no matter which node they connect to. For this to happen, whenever data is written to one node, it must be instantly forwarded or replicated to all the other nodes in the system before the write is deemed ‘successful’. Consistency as defined in the CAP theorem is quite different from the consistency guaranteed in ACID database transactions.
AvailabilityEvery request received by a non-failing node in the system must result in a response, without the guarantee that it contains the most recent version of the data. This is the definition of availability in CAP theorem as defined by Gilbert and Lynch. Availability as defined in CAP theorem is different from high availability in software architecture.
Partition toleranceThe system continues to operate despite an arbitrary number of messages being dropped by the network between nodes.
