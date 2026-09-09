# Q&A About License

## Why is MiniMax-H3's open-weight license currently limited to the EU, UK, South Korea, and US?

MiniMax-H3 was built with the goal of global availability. The current territory scope is not about excluding specific countries or regions, but about recognizing that video generation models are facing a more complex and rapidly evolving regulatory environment compared with text or code models.

Regions such as the EU, UK, South Korea, and the US are currently developing or enforcing AI-related regulations that may have specific implications for generative video models, especially around areas such as likeness generation, copyright, content safety, and responsible deployment.

- The EU AI Act has started enforcement, while practical requirements for models capable of generating video and likeness-related content are still evolving.
- Similar regulatory uncertainties exist in the UK and South Korea regarding AI-generated content and video generation.
- In the US, AI regulation remains a rapidly changing landscape, and MiniMax is also involved in ongoing copyright-related legal proceedings specifically concerning generative video AI.

For open-weight models, once the weights are released, developers can deploy and modify them independently. This creates different compliance challenges compared with hosted services.

We had two options:

1. Wait until every jurisdiction reaches complete regulatory clarity before releasing open weights, which could take a long time while AI technology continues to evolve.
2. Release the model now with a transparent license scope, while continuing to evaluate and expand availability.

We chose the second approach. The current limitation means "not yet", not "not ever."

## Why can MiniMax-H3 API be used globally if open weights are restricted in some regions?

The difference is the distribution model.

The main concern is not the existence of MiniMax-H3 itself, but the ability to control compliance after open weights leave our infrastructure.

For API access, MiniMax operates the serving infrastructure and can enforce appropriate safeguards, including:

- Protection against misuse involving minors.
- Copyright-related compliance measures.
- Content safety controls.
- Compliance with applicable laws and regulations.

With open weights, users can independently deploy, modify, and distribute the model, which makes it much harder to ensure the same level of compliance.

Therefore, the API and open-weight release follow different approaches:

- API: Globally available with built-in safeguards and responsible-use controls.
- Open weights: Temporarily limited in certain regions until the regulatory and compliance framework becomes clearer.

## Can organizations in restricted regions still use MiniMax-H3?

Yes.

Organizations in these regions can apply for a formal license. After reviewing the deployment scenario and confirming that appropriate compliance controls and safeguards are implemented, MiniMax may authorize usage.

[Application form](https://platform.minimax.io/h3-license)

Through authorized deployments, MiniMax can ensure that MiniMax-H3 is used responsibly while meeting local legal and regulatory requirements.

## Will MiniMax expand open-weight availability in the future?

Yes. We will continue monitoring legal developments and reassessing the territory scope.

Our commitments:

- Continuously review regulations and compliance requirements across regions.
- Keep MiniMax-H3 API available globally, so users can continue accessing the model.
- Clearly communicate any future license changes instead of making silent updates.
- Listen to feedback from developers, researchers, and organizations affected by these restrictions.

Our goal remains the same: bringing intelligence to everyone with responsible AI use.

The current license scope reflects today's regulatory reality, not our long-term vision.
