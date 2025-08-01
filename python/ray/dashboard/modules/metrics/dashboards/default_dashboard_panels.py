# ruff: noqa: E501

from ray.dashboard.modules.metrics.dashboards.common import (
    DashboardConfig,
    Panel,
    Target,
)

"""
Queries for autoscaler resources.
"""
# Note: MAX & USED resources are reported from raylet to provide the most up to date information.
# But MAX + PENDING data is coming from the autoscaler. That said, MAX + PENDING can be
# more outdated. it is harmless because the actual MAX will catch up with MAX + PENDING
# eventually.
MAX_CPUS = 'sum(autoscaler_cluster_resources{{resource="CPU",{global_filters}}})'
PENDING_CPUS = 'sum(autoscaler_pending_resources{{resource="CPU",{global_filters}}})'
MAX_GPUS = 'sum(autoscaler_cluster_resources{{resource="GPU",{global_filters}}})'
PENDING_GPUS = 'sum(autoscaler_pending_resources{{resource="GPU",{global_filters}}})'


def max_plus_pending(max_resource, pending_resource):
    return f"({max_resource} or vector(0)) + ({pending_resource} or vector(0))"


MAX_PLUS_PENDING_CPUS = max_plus_pending(MAX_CPUS, PENDING_CPUS)
MAX_PLUS_PENDING_GPUS = max_plus_pending(MAX_GPUS, PENDING_GPUS)


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# IMPORTANT: Please keep this in sync with Metrics.tsx and ray-metrics.rst
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEFAULT_GRAFANA_PANELS = [
    Panel(
        id=26,
        title="Scheduler Task State",
        description="Current number of tasks in a particular state.\n\nState: the task state, as described by rpc::TaskState proto in common.proto. Task resubmissions due to failures or object reconstruction are shown with (retry) in the label.",
        unit="tasks",
        targets=[
            Target(
                expr='sum(max_over_time(ray_tasks{{IsRetry="0",State=~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}[14d])) by (State) or clamp_min(sum(ray_tasks{{IsRetry="0",State!~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}) by (State), 0)',
                legend="{{State}}",
            ),
            Target(
                expr='sum(max_over_time(ray_tasks{{IsRetry!="0",State=~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}[14d])) by (State) or clamp_min(sum(ray_tasks{{IsRetry!="0",State!~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}) by (State), 0)',
                legend="{{State}} (retry)",
            ),
        ],
        fill=0,
        stack=False,
    ),
    Panel(
        id=35,
        title="Requested Live Tasks by Name",
        description="Current number of (live) tasks with a particular name. Task resubmissions due to failures or object reconstruction are shown with (retry) in the label.",
        unit="tasks",
        targets=[
            Target(
                expr='clamp_min(sum(ray_tasks{{IsRetry="0",State!~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}) by (Name), 0)',
                legend="{{Name}}",
            ),
            Target(
                expr='clamp_min(sum(ray_tasks{{IsRetry!="0",State!~"FINISHED|FAILED",instance=~"$Instance",{global_filters}}}) by (Name), 0)',
                legend="{{Name}} (retry)",
            ),
        ],
        fill=0,
        stack=False,
    ),
    Panel(
        id=38,
        title="Running Tasks by Name",
        description="Current number of (running) tasks with a particular name. Task resubmissions due to failures or object reconstruction are shown with (retry) in the label.",
        unit="tasks",
        targets=[
            Target(
                expr='clamp_min(sum(ray_tasks{{IsRetry="0",State=~"RUNNING*",instance=~"$Instance",{global_filters}}}) by (Name), 0)',
                legend="{{Name}}",
            ),
            Target(
                expr='clamp_min(sum(ray_tasks{{IsRetry!="0",State=~"RUNNING*",instance=~"$Instance",{global_filters}}}) by (Name), 0)',
                legend="{{Name}} (retry)",
            ),
        ],
        fill=0,
        stack=False,
    ),
    Panel(
        id=33,
        title="Scheduler Actor State",
        description='Note: not impacted by "Instance" variable.\n\nCurrent number of actors in a particular state.\n\nState: the actor state, as described by rpc::ActorTableData proto in gcs.proto.',
        unit="actors",
        targets=[
            Target(
                expr='sum(ray_actors{{Source="gcs",{global_filters}}}) by (State)',
                legend="{{State}}",
            )
        ],
    ),
    Panel(
        id=42,
        title="Live Actor State",
        description="Current number of alive actors in a particular state.\n\nState: IDLE, RUNNING_TASK, RUNNING_IN_RAY_GET, RUNNING_IN_RAY_WAIT",
        unit="actors",
        targets=[
            Target(
                expr='sum(ray_actors{{Source="executor",NodeAddress=~"$Instance",{global_filters}}}) by (State)',
                legend="{{State}}",
            )
        ],
    ),
    Panel(
        id=36,
        title="Live Actors by Name",
        description="Current number of alive actors with a particular name.",
        unit="actors",
        targets=[
            Target(
                expr='sum(ray_actors{{State!="DEAD",Source="executor",NodeAddress=~"$Instance",{global_filters}}}) by (Name)',
                legend="{{Name}}",
            )
        ],
    ),
    Panel(
        id=27,
        title="Scheduler CPUs (logical slots)",
        description="Logical CPU usage of Ray. The dotted line indicates the total number of CPUs. The logical CPU is allocated by `num_cpus` arguments from tasks and actors. PENDING means the number of CPUs that will be available when new nodes are up after the autoscaler scales up.\n\nNOTE: Ray's logical CPU is different from physical CPU usage. Ray's logical CPU is allocated by `num_cpus` arguments.",
        unit="cores",
        targets=[
            Target(
                expr='sum(ray_resources{{Name="CPU",State="USED",instance=~"$Instance",{global_filters}}}) by (instance)',
                legend="CPU Usage: {{instance}}",
            ),
            Target(
                expr='sum(ray_resources{{Name="CPU",instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
            # If max + pending > max, we display this value.
            # (A and predicate) means to return A when the predicate satisfies in PromSql.
            Target(
                expr=f"({MAX_PLUS_PENDING_CPUS} and {MAX_PLUS_PENDING_CPUS} > ({MAX_CPUS} or vector(0)))",
                legend="MAX + PENDING",
            ),
        ],
    ),
    Panel(
        id=29,
        title="Object Store Memory",
        description="Object store memory usage by location. The dotted line indicates the object store memory capacity.\n\nLocation: where the memory was allocated, which is MMAP_SHM or MMAP_DISK to indicate memory-mapped page, SPILLED to indicate spillage to disk, and WORKER_HEAP for objects small enough to be inlined in worker memory. Refer to metric_defs.cc for more information.",
        unit="bytes",
        targets=[
            Target(
                expr='sum(ray_object_store_memory{{instance=~"$Instance",{global_filters}}}) by (Location)',
                legend="{{Location}}",
            ),
            Target(
                expr='sum(ray_resources{{Name="object_store_memory",instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=28,
        title="Scheduler GPUs (logical slots)",
        description="Logical GPU usage of Ray. The dotted line indicates the total number of GPUs. The logical GPU is allocated by `num_gpus` arguments from tasks and actors. PENDING means the number of GPUs that will be available when new nodes are up after the autoscaler scales up.",
        unit="GPUs",
        targets=[
            Target(
                expr='sum(ray_resources{{Name="GPU",State="USED",instance=~"$Instance",{global_filters}}}) by (instance)',
                legend="GPU Usage: {{instance}}",
            ),
            Target(
                expr='sum(ray_resources{{Name="GPU",instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
            # If max + pending > max, we display this value.
            # (A and predicate) means to return A when the predicate satisfies in PromSql.
            Target(
                expr=f"({MAX_PLUS_PENDING_GPUS} and {MAX_PLUS_PENDING_GPUS} > ({MAX_GPUS} or vector(0)))",
                legend="MAX + PENDING",
            ),
        ],
    ),
    Panel(
        id=40,
        title="Scheduler Placement Groups",
        description='Note: not impacted by "Instance" variable.\n\nCurrent number of placement groups in a particular state.\n\nState: the placement group state, as described by the rpc::PlacementGroupTable proto in gcs.proto.',
        unit="placement groups",
        targets=[
            Target(
                expr="sum(ray_placement_groups{{{global_filters}}}) by (State)",
                legend="{{State}}",
            )
        ],
    ),
    Panel(
        id=2,
        title="Node CPU (hardware utilization)",
        description="",
        unit="cores",
        targets=[
            Target(
                expr='sum(ray_node_cpu_utilization{{instance=~"$Instance", IsHeadNode="false", {global_filters}}} * ray_node_cpu_count{{instance=~"$Instance",{global_filters}}} / 100) by (instance)',
                legend="CPU Usage: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_cpu_utilization{{instance=~"$Instance", IsHeadNode="true", {global_filters}}} * ray_node_cpu_count{{instance=~"$Instance",{global_filters}}} / 100) by (instance)',
                legend="CPU Usage: {{instance}} (head)",
            ),
            Target(
                expr='sum(ray_node_cpu_count{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=8,
        title="Node GPU (hardware utilization)",
        description="Node's physical (hardware) GPU usage. The dotted line means the total number of hardware GPUs from the cluster. ",
        unit="GPUs",
        targets=[
            Target(
                expr='sum(ray_node_gpus_utilization{{instance=~"$Instance", IsHeadNode="false", {global_filters}}} / 100) by (instance, GpuIndex, GpuDeviceName)',
                legend="GPU Usage: {{instance}}, gpu.{{GpuIndex}}, {{GpuDeviceName}}",
            ),
            Target(
                expr='sum(ray_node_gpus_utilization{{instance=~"$Instance", IsHeadNode="true", {global_filters}}} / 100) by (instance, GpuIndex, GpuDeviceName)',
                legend="GPU Usage: {{instance}} (head), gpu.{{GpuIndex}}, {{GpuDeviceName}}",
            ),
            Target(
                expr='sum(ray_node_gpus_available{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=6,
        title="Node Disk",
        description="Node's physical (hardware) disk usage. The dotted line means the total amount of disk space from the cluster.\n\nNOTE: When Ray is deployed within a container, this shows the disk usage from the host machine. ",
        unit="bytes",
        targets=[
            Target(
                expr='sum(ray_node_disk_usage{{instance=~"$Instance", IsHeadNode="false", {global_filters}}}) by (instance)',
                legend="Disk Used: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_disk_usage{{instance=~"$Instance", IsHeadNode="true", {global_filters}}}) by (instance)',
                legend="Disk Used: {{instance}} (head)",
            ),
            Target(
                expr='sum(ray_node_disk_free{{instance=~"$Instance",{global_filters}}}) + sum(ray_node_disk_usage{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=32,
        title="Node Disk IO Speed",
        description="Disk IO per node.",
        unit="Bps",
        targets=[
            Target(
                expr='sum(ray_node_disk_io_write_speed{{instance=~"$Instance", IsHeadNode="false", {global_filters}}}) by (instance)',
                legend="Write: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_disk_io_write_speed{{instance=~"$Instance", IsHeadNode="true", {global_filters}}}) by (instance)',
                legend="Write: {{instance}} (head)",
            ),
            Target(
                expr='sum(ray_node_disk_io_read_speed{{instance=~"$Instance", IsHeadNode="false", {global_filters}}}) by (instance)',
                legend="Read: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_disk_io_read_speed{{instance=~"$Instance", IsHeadNode="true", {global_filters}}}) by (instance)',
                legend="Read: {{instance}} (head)",
            ),
        ],
    ),
    Panel(
        id=4,
        title="Node Memory (heap + object store)",
        description="The physical (hardware) memory usage for each node. The dotted line means the total amount of memory from the cluster. Node memory is a sum of object store memory (shared memory) and heap memory.\n\nNote: If Ray is deployed within a container, the total memory could be lower than the host machine because Ray may reserve some additional memory space outside the container.",
        unit="bytes",
        targets=[
            Target(
                expr='sum(ray_node_mem_used{{instance=~"$Instance", IsHeadNode="false", {global_filters}}}) by (instance)',
                legend="Memory Used: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_mem_used{{instance=~"$Instance", IsHeadNode="true", {global_filters}}}) by (instance)',
                legend="Memory Used: {{instance}} (head)",
            ),
            Target(
                expr='sum(ray_node_mem_total{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=48,
        title="Node Memory Percentage (heap + object store)",
        description="The percentage of physical (hardware) memory usage for each node.",
        unit="%",
        targets=[
            Target(
                expr='sum(ray_node_mem_used{{instance=~"$Instance", IsHeadNode="false", {global_filters}}}/ray_node_mem_total{{instance=~"$Instance", IsHeadNode="false", {global_filters}}} * 100) by (instance)',
                legend="Memory Used: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_mem_used{{instance=~"$Instance", IsHeadNode="true", {global_filters}}}/ray_node_mem_total{{instance=~"$Instance", IsHeadNode="true", {global_filters}}} * 100) by (instance)',
                legend="Memory Used: {{instance}} (head)",
            ),
        ],
        fill=0,
        stack=False,
    ),
    Panel(
        id=44,
        title="Node Out of Memory Failures by Name",
        description="The number of tasks and actors killed by the Ray Out of Memory killer due to high memory pressure. Metrics are broken down by IP and the name. https://docs.ray.io/en/master/ray-core/scheduling/ray-oom-prevention.html.",
        unit="failures",
        targets=[
            Target(
                expr='sum(ray_memory_manager_worker_eviction_total{{instance=~"$Instance",{global_filters}}}) by (Name, instance)',
                legend="OOM Killed: {{Name}}, {{instance}}",
            ),
        ],
    ),
    Panel(
        id=34,
        title="Node Memory by Component",
        description="The physical (hardware) memory usage across the cluster, broken down by component. This reports the summed RSS-SHM per Ray component, which corresponds to an approximate memory usage per proc. Ray components consist of system components (e.g., raylet, gcs, dashboard, or agent) and the process (that contains method names) names of running tasks/actors.",
        unit="bytes",
        targets=[
            Target(
                expr='(sum(ray_component_rss_mb{{instance=~"$Instance",{global_filters}}} * 1e6) by (Component)) - (sum(ray_component_mem_shared_bytes{{instance=~"$Instance",{global_filters}}}) by (Component))',
                legend="{{Component}}",
            ),
            Target(
                expr='sum(ray_node_mem_shared_bytes{{instance=~"$Instance",{global_filters}}})',
                legend="shared_memory",
            ),
            Target(
                expr='sum(ray_node_mem_total{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=37,
        title="Node CPU by Component",
        description="The physical (hardware) CPU usage across the cluster, broken down by component. This reports the summed CPU usage per Ray component. Ray components consist of system components (e.g., raylet, gcs, dashboard, or agent) and the process (that contains method names) names of running tasks/actors.",
        unit="cores",
        targets=[
            Target(
                # ray_component_cpu_percentage returns a percentage that can be > 100. It means that it uses more than 1 CPU.
                expr='sum(ray_component_cpu_percentage{{instance=~"$Instance",{global_filters}}}) by (Component) / 100',
                legend="{{Component}}",
            ),
            Target(
                expr='sum(ray_node_cpu_count{{instance=~"$Instance",{global_filters}}})',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=18,
        title="Node GPU Memory (GRAM)",
        description="The physical (hardware) GPU memory usage for each node. The dotted line means the total amount of GPU memory from the cluster.",
        unit="bytes",
        targets=[
            Target(
                expr='sum(ray_node_gram_used{{instance=~"$Instance",{global_filters}}} * 1024 * 1024) by (instance, GpuIndex, GpuDeviceName)',
                legend="Used GRAM: {{instance}}, gpu.{{GpuIndex}}, {{GpuDeviceName}}",
            ),
            Target(
                expr='(sum(ray_node_gram_available{{instance=~"$Instance",{global_filters}}}) + sum(ray_node_gram_used{{instance=~"$Instance",{global_filters}}})) * 1024 * 1024',
                legend="MAX",
            ),
        ],
    ),
    Panel(
        id=50,
        title="Node TPU Tensorcore Utilization (Percentage)",
        description="Percentage of tensorcore utilization for the TPUs on this node. Computed by dividing the number of tensorcore operations by the maximum supported number of operations during the sample period.",
        unit="%",
        targets=[
            Target(
                expr='sum(ray_tpu_tensorcore_utilization{{instance=~"$Instance",{global_filters}}}) by (instance, TpuIndex, TpuDeviceName, TpuType, TpuTopology)',
                legend="{{instance}}, tpu.{{TpuIndex}}, {{TpuType}}, {{TpuTopology}}",
            ),
        ],
    ),
    Panel(
        id=51,
        title="Node TPU High Bandwidth Memory Utilization (Percentage)",
        description="Percentage of bandwidth memory utilization for the TPUs on this node. Computed by dividing the memory bandwidth used by the maximum supported memory bandwidth limit during the sample period.",
        unit="%",
        targets=[
            Target(
                expr='sum(ray_tpu_memory_bandwidth_utilization{{instance=~"$Instance",{global_filters}}}) by (instance, TpuIndex, TpuDeviceName, TpuType, TpuTopology)',
                legend="{{instance}}, tpu.{{TpuIndex}}, {{TpuType}}, {{TpuTopology}}",
            ),
        ],
    ),
    Panel(
        id=52,
        title="Node TPU Duty Cycle (Percentage)",
        description="Percentage of time over the sample period during which the TPU is actively processing.",
        unit="%",
        targets=[
            Target(
                expr='sum(ray_tpu_duty_cycle{{instance=~"$Instance",{global_filters}}}) by (instance, TpuIndex, TpuDeviceName, TpuType, TpuTopology) or vector(0)',
                legend="{{instance}}, tpu.{{TpuIndex}}, {{TpuType}}, {{TpuTopology}}",
            ),
        ],
    ),
    Panel(
        id=53,
        title="Node TPU Memory Used",
        description="Total memory used/allocated for the TPUs on this node.",
        unit="bytes",
        targets=[
            Target(
                expr='sum(ray_tpu_memory_used{{instance=~"$Instance",{global_filters}}}) by (instance, TpuIndex, TpuDeviceName, TpuType, TpuTopology) or vector(0)',
                legend="Memory Used: {{instance}}, tpu.{{TpuIndex}}, {{TpuType}}, {{TpuTopology}}",
            ),
            Target(
                expr='sum(ray_tpu_memory_total{{instance=~"$Instance",{global_filters}}}) by (instance, TpuIndex, TpuDeviceName, TpuType, TpuTopology) or vector(0)',
                legend="Memory Total: {{instance}}, tpu.{{TpuIndex}}, {{TpuType}}, {{TpuTopology}}",
            ),
        ],
    ),
    Panel(
        id=20,
        title="Node Network",
        description="Network speed per node",
        unit="Bps",
        targets=[
            Target(
                expr='sum(ray_node_network_receive_speed{{instance=~"$Instance",{global_filters}}}) by (instance)',
                legend="Recv: {{instance}}",
            ),
            Target(
                expr='sum(ray_node_network_send_speed{{instance=~"$Instance",{global_filters}}}) by (instance)',
                legend="Send: {{instance}}",
            ),
        ],
    ),
    Panel(
        id=24,
        title="Node Count",
        description='Note: not impacted by "Instance" variable.\n\nA total number of active failed, and pending nodes from the cluster. \n\nACTIVE: A node is alive and available.\n\nFAILED: A node is dead and not available. The node is considered dead when the raylet process on the node is terminated. The node will get into the failed state if it cannot be provided (e.g., there\'s no available node from the cloud provider) or failed to setup (e.g., setup_commands have errors). \n\nPending: A node is being started by the Ray cluster launcher. The node is unavailable now because it is being provisioned and initialized.',
        unit="nodes",
        targets=[
            Target(
                expr="sum(autoscaler_active_nodes{{{global_filters}}}) by (NodeType)",
                legend="Active Nodes: {{NodeType}}",
            ),
            Target(
                expr="sum(autoscaler_recently_failed_nodes{{{global_filters}}}) by (NodeType)",
                legend="Failed Nodes: {{NodeType}}",
            ),
            Target(
                expr="sum(autoscaler_pending_nodes{{{global_filters}}}) by (NodeType)",
                legend="Pending Nodes: {{NodeType}}",
            ),
        ],
    ),
    Panel(
        id=41,
        title="Cluster Utilization",
        description="Aggregated utilization of all physical resources (CPU, GPU, memory, disk, or etc.) across the cluster.",
        unit="%",
        targets=[
            # CPU
            Target(
                expr='avg(ray_node_cpu_utilization{{instance=~"$Instance",{global_filters}}})',
                legend="CPU (physical)",
            ),
            # GPU
            Target(
                expr='sum(ray_node_gpus_utilization{{instance=~"$Instance",{global_filters}}}) / on() (sum(ray_node_gpus_available{{instance=~"$Instance",{global_filters}}}) or vector(0))',
                legend="GPU (physical)",
            ),
            # Memory
            Target(
                expr='sum(ray_node_mem_used{{instance=~"$Instance",{global_filters}}}) / on() (sum(ray_node_mem_total{{instance=~"$Instance",{global_filters}}})) * 100',
                legend="Memory (RAM)",
            ),
            # GRAM
            Target(
                expr='sum(ray_node_gram_used{{instance=~"$Instance",{global_filters}}}) / on() (sum(ray_node_gram_available{{instance=~"$Instance",{global_filters}}}) + sum(ray_node_gram_used{{instance=~"$Instance",{global_filters}}})) * 100',
                legend="GRAM",
            ),
            # Object Store
            Target(
                expr='sum(ray_object_store_memory{{instance=~"$Instance",{global_filters}}}) / on() sum(ray_resources{{Name="object_store_memory",instance=~"$Instance",{global_filters}}}) * 100',
                legend="Object Store Memory",
            ),
            # Disk
            Target(
                expr='sum(ray_node_disk_usage{{instance=~"$Instance",{global_filters}}}) / on() (sum(ray_node_disk_free{{instance=~"$Instance",{global_filters}}}) + sum(ray_node_disk_usage{{instance=~"$Instance",{global_filters}}})) * 100',
                legend="Disk",
            ),
        ],
        fill=0,
        stack=False,
    ),
    Panel(
        id=45,
        title="Node GPU by Component",
        description="The physical (hardware) GPU usage across the cluster, broken down by component. This reports the summed GPU usage per Ray component.",
        unit="GPUs",
        targets=[
            Target(
                expr="sum(ray_component_gpu_percentage{{{global_filters}}} / 100) by (Component)",
                legend="{{Component}}",
            ),
        ],
    ),
    Panel(
        id=46,
        title="Node GPU Memory by Component",
        description="The physical (hardware) GPU memory usage across the cluster, broken down by component. This reports the summed GPU memory usage per Ray component.",
        unit="bytes",
        targets=[
            Target(
                expr="sum(ray_component_gpu_memory_mb{{{global_filters}}}) by (Component)",
                legend="{{Component}}",
            ),
            Target(
                expr='(sum(ray_node_gram_available{{instance=~"$Instance",{global_filters}}}) + sum(ray_node_gram_used{{instance=~"$Instance",{global_filters}}}))*1024*1024',
                legend="MAX",
            ),
        ],
    ),
]


ids = []
for panel in DEFAULT_GRAFANA_PANELS:
    ids.append(panel.id)
assert len(ids) == len(
    set(ids)
), f"Duplicated id found. Use unique id for each panel. {ids}"

default_dashboard_config = DashboardConfig(
    name="DEFAULT",
    default_uid="rayDefaultDashboard",
    panels=DEFAULT_GRAFANA_PANELS,
    standard_global_filters=[
        'SessionName=~"$SessionName"',
        'ray_io_cluster=~"$Cluster"',
    ],
    base_json_file_name="default_grafana_dashboard_base.json",
)
