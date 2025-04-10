# NoProp =/= No gradient
[NoProp: Training Neural Networks without Back-propagation or Forward-propagation](https://arxiv.org/html/2503.24322v1)

The paper's title might suggest it's about gradient-free methods, but it actually tackles a different problem. Neural networks are sequential by design—each layer depends on the previous one's output, preventing parallel computation across layers. This paper introduces a way to bypass this limitation, allowing neural networks to be trained in parallel across layers while still using backpropagation within each layer.

### Diffusion models are sequential but separable
Like neural networks, diffusion models are sequential—they trace a path from random noise to a data point through multiple time steps. Training these models requires optimizing across this entire path, which would create an enormous computational graph (imagine evaluating a DiT over 1,000 steps as a single graph).
Fortunately, diffusion models have a key advantage: they're separable. This means we can train each time step independently, keeping the computational graph at a manageable size instead of scaling with the number of steps.

### Neural nets also have "time" and can be made separable
A neural network can be viewed as a sequential process where "time" represents the layers. This paper reframes neural networks as diffusion processes. In this approach, each layer acts as a denoising step in the output space.
The approach is flexible—a "layer" could even be an entire neural network itself. We're essentially performing diffusion in a predefined space for our desired output. This allows us to increase the effective computational graph at inference time while keeping our training graphs small, thanks to separability.

The paper offers several formulations for this diffusion training process, including discrete and continuous time diffusion, as well as flow matching. You should check the paper out for full details.

### Doing this, we lose the hierarchy of NN representations
Traditional neural networks build hierarchical representations, with each layer creating increasingly abstract features as you go deeper. However, when treating neural nets as diffusion processes, layer representations exist in the same space as the output. This means the diffusion latents must carry much more representational burden, as each layer can only perform a denoising step.
This approach also requires manually designing the latent representations. For instance, in traditional classification networks, the intermediate representations are learned automatically from data. But in this diffusion-based approach, you must explicitly define the output representation (such as embedding dimension) and only train toward that final outcome.

### Some half-baked thoughts on residual streams in transformers
Transformers also operate in the same space as their output through what's known as the residual stream. Each transformer layer produces a linear update to the original input vector. We can view this as layers tracing a path in embedding space between the current token and the next token (assuming next-token prediction). This raises an interesting question: how does this approach differ from the diffusion formulation described above?

