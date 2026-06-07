# Attention

The transformer mechanism by which each token "looks back" at earlier tokens — comparing itself against every other token — to decide what to focus on and generate next. For N tokens that's N×N comparisons (the core source of cost), and each new token needs all earlier tokens' representations.
