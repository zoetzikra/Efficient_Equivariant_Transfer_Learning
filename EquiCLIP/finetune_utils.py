import torch
import wandb

from tqdm import tqdm
from exp_utils import group_transform_images, random_transformed_images
from weighted_equitune_utils import get_output

def cycle(iterable):
    while True:
        for x in iterable:
            yield x


def accuracy(output, target, topk=(1,)):
    pred = output.topk(max(topk), 1, True, True)[1].t()  # dim [max_topk, batch_size]
    correct = pred.eq(target.view(1, -1).expand_as(pred))
    return [float(correct[:k].reshape(-1).float().sum(0, keepdim=True).cpu().numpy()) for k in topk]

def finetune_clip(args, model, optimizer, criterion, zeroshot_weights, loader, data_transformations="", group_name="",
                  num_iterations=100, iter_print_freq=10, device="cuda:0"):
    import time
    torch.autograd.set_detect_anomaly(True)
    since = time.time()
    top1, top5, n = 0., 0., 0.
    training_iterator = cycle(iter(loader))
    # for i, (images, target) in enumerate(tqdm(loader)):
    import time
    st_time = time.time()
    for i in range(num_iterations):
        if (i+1)%iter_print_freq == 0:
            print(f"iteration number: {i+1}")
            curr_time = time.time()
            print(f"time elapsed per iter: {(curr_time - st_time) / (i+1)}")
        (images, target) = next(training_iterator)
        images = images.to(device)  # dim [batch_size, c_in, H, H]
        images = random_transformed_images(images, data_transformations=data_transformations)  # randomly transform data

        # images = torch.rot90(images, k=1, dims=(-2, -1))
        group_images = group_transform_images(images,
                                              group_name=group_name)  # dim [group_size, batch_size, c_in, H, H]
        group_images_shape = group_images.shape

        # dim [group_size * batch_size, c_in, H, H]
        group_images = group_images.reshape(group_images_shape[0] * group_images_shape[1], group_images_shape[2],
                                            group_images_shape[3], group_images_shape[3])
        # print(f"images.shape: {images.shape}")
        target = target.to(device)
        # print(f"target.shape: {target.shape}")

        # zero the parameter gradients
        optimizer.zero_grad()

        # predict
        image_features = model.encode_image(group_images)  # dim [group_size * batch_size, feat_size=512]
        # print(f"image_features.shape: {image_features.shape}")
        image_features_norm = image_features.clone().norm(dim=-1, keepdim=True)
        image_features = image_features / image_features_norm
        # zeroshot weights correspond to text features for all possible classes
        # logits = 100. * image_features @ zeroshot_weights  # dim [group_size * batch_size, num_classes=1000]
        logits = args.logit_factor * image_features @ zeroshot_weights  # dim [group_size * batch_size, num_classes=1000]
        # logits = -torch.nn.functional.softmax(-logits, dim=-1)
        if args.softmax:
            logits = torch.nn.functional.softmax(logits, dim=-1)
        # print(f"logits.shape: {logits.shape}")

        # measure accuracy
        if args.method == "equitune":
            output = get_output(logits, group_name=group_name, reduction="mean")
        elif args.method == "equizero":
            equitune_output = get_output(logits, group_name=group_name, reduction="mean")
            equi0_output = get_output(logits, group_name=group_name, reduction="max")
            output = equitune_output + (equi0_output - equitune_output).detach()
        else:
            output = logits

        ## backprop
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()

        wandb.log({"loss": loss.item()})

    return model