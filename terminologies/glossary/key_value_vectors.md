# Key / Value vectors

The per-token **key** and **value** float vectors that attention reads (both derived from a token's embedding — not the token itself). The **key** is matched against a query via dot product to decide *how much* attention each token gets; the **value** is the payload those weights sum over to decide *what* information is passed on.
