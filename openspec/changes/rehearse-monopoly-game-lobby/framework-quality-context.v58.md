# Read-only framework quality SDK source export

Exact UTF-8 source and SHA256 from the existing verification host. Paths are host-relative. Reference only; the existing SDK test suite is NOT authorized for execution. No SDK or host assembly files are changed.

## Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/Defines/QualityDetail.cs

SHA256: c1e742a87c97c47f84f3e5561033c6cedbb5d5c004c4da2fb8034e648e3bc7b4

```csharp
using System.Collections.Generic;

namespace jj.Core.Runtime
{
    /// <summary>
    /// APM系列服务使用的画质参数结构体
    /// </summary>
    public struct QualityDetail
    {
        /// <summary>
        /// 画质参数对应配置的画质等级关键字，在画质匹配配置中定义，也可以自定义
        /// </summary>
        public string name;

        /// <summary>
        /// 画质参数 [参数名称] 到 [参数数值] 的映射表
        /// 目前预定义的参数名如下：
        /// shader_lod		对应Unity下Shader.globalMaximumLOD
        /// msaa			对应MSAA等级，1为关闭，2为2x，4为4x，8为8x
        /// post_aa			对应URP下后处理AA，0为关闭，1为FXAA，2为SMAA，3为TAA（对应AntialiasingMode枚举）
        /// unity_quality	对应Unity下QualitySettings.SetQualityLevel，也就是QualitySettings配置中各项配置的下标索引[0 ~ 最大数量-1]
        /// screen_resolution	对应Unity下的全局分辨率（Screen.SetResolution），数值取高度，宽度会通过高度和宽高比计算出来
        /// 预定义以外的参数需要通过定制处理模块（实现IQualityHandler接口）来处理。
        /// </summary>
        public Dictionary<string, int> detailMap;
    }

    /// <summary>
    /// 
    /// </summary>
    public struct QualityAdaptDetail
    {
        public string name;
        public Dictionary<string, int> deltaMap;
        public Dictionary<string, int> absoluteMap;
    }
}
```

## Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IDeviceRatingService.cs

SHA256: 885257548ff5bb54cd9a4c640b5821a19f51293db6c6dfdc0d81946ded3fa3f5

```csharp
using Cysharp.Threading.Tasks;
using UnityEngine;

namespace jj.Core.Runtime
{
    /// <summary>
    /// 设备分级服务，根据当前运行设备的硬件型号参数，以及分级配置中设置的分级规则，计算当前运行设备最佳匹配的分级档位。
    /// 设备型号参数通过<see cref="ISystemInfoService"/>服务获取。
    /// <seealso cref="ISystemInfoService"/>
    /// </summary>
    [BusinessDomain(BusinessDomain.OpenSource)]
    public interface IDeviceRatingService : IServiceBase
    {
        /// <summary>
        /// 执行分级，返回当前运行设备最佳匹配的分级档位。
        /// 分级的结果也可以通过<see cref="GetDeviceRating"/>获取。
        /// 注意，本接口为异步接口，不要同步依赖接口的执行结果。
        /// <seealso cref="GetDeviceRating"/>
        /// <seealso cref="GetDeviceRatingKey"/>
        /// </summary>
        /// <param name="configObj">分级配置的ScriptableObject形式，必要参数</param>
        /// <returns>设备适配档位，取值来自分级配置里定义的档位ID，失败则返回 -1</returns>
        public UniTask<int> DoRatingAsync(ScriptableObject configObj);

        public int DoRating(ScriptableObject configObj);

        /// <summary>
        /// 获取上一次执行分级的结果（当前运行设备最佳适配的分级档位）。
        /// <seealso cref="GetDeviceRatingKey"/>
        /// </summary>
        /// <returns>设备适配档位，取值来自分级配置里定义的档位ID，失败则返回 -1</returns>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetDeviceRating();

        /// <summary>
        /// 获取上一次执行分级的结果（当前运行设备最佳适配的分级档位）所对应的文本标签（分级配置文件中配置的ratingkeys）。
        /// <seealso cref="GetDeviceRating"/>
        /// </summary>
        /// <returns>设备适配档位的文本标签，失败则返回空字符串</returns>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetDeviceRatingKey();
        
        public int GetRemoteMatch();

        /// <summary>
        /// 获取上一次执行分级的结果（当前运行设备最佳适配的分级档位）所对应的下标（第几档）。
        /// </summary>
        /// <returns>设备适配档位的下标</returns>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetIndex();

        /// <summary>
        /// 获取当前运行设备的设备信息。如果没有执行过设备分级，将返回null
        /// </summary>
        /// <returns>设备信息</returns>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public APMDefine.DeviceInfo? GetDeviceInfo();

        /// <summary>
        /// 设置当前运行设备的设备信息，将会用在执行设备分级时作为分级依据。
        /// <seealso cref="APMDefine.DeviceInfo"/>
        /// </summary>
        /// <param name="deviceInfo">设备信息</param>
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public void SetDeviceInfo(APMDefine.DeviceInfo deviceInfo);

        /// <summary>
        /// 获取本地持久化存储的数值
        /// </summary>
        /// <returns></returns>
        public DeviceScore GetDeviceScoreLocal();
        
        /// <summary>
        /// 释放资源
        /// </summary>
        public void Release();
    }

    public partial class FakeDeviceRatingService : IDeviceRatingService
    {
        public void OnStart()
        {
        }

        public void OnDestroy()
        {

#region GeneratedBreak
            Context.Break();
#endregion
        }
        public bool IsInited ()
        {
            return false;
        }
        public bool IsImmortal()
        {
            return false;
        }

        public bool IsServiceInited ()
        {
            throw new System.NotImplementedException();
        }

        public async UniTask<int> DoRatingAsync(ScriptableObject configObj)
        {
            return 2;
        }

        public int DoRating(ScriptableObject configObj)
        {
            return 2;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetDeviceRating()
        {
            return 2;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetDeviceRatingKey()
        {
            return string.Empty;
        }

        public int GetRemoteMatch()
        {
            return 0;
        }

        public string GetDeviceRatingKey(int rating)
        {
            return string.Empty;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetIndex()
        {
            return 2;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public APMDefine.DeviceInfo? GetDeviceInfo()
        {
            return null;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public void SetDeviceInfo(APMDefine.DeviceInfo deviceInfo)
        {
        }

        public void RegisterStoreRemoteScoreCallback(System.Action<DeviceScore> callback)
        {
        }

        public void DeregisterStoreRemoteScoreCallback(System.Action<DeviceScore> callback)
        {
        }

        public DeviceScore GetDeviceScoreLocal()
        {
            return new DeviceScore();
        }

        public void Release() { }
    }
}

```

## Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IQualityMatchingService.cs

SHA256: ae426a4d967e8880c55b5c57fc6bf60706fa5125f5617605e932de64aafc5a8e

```csharp
using UnityEngine;

namespace jj.Core.Runtime
{
    /// <summary>
    /// Matches quality parameters to the device rating key using a QualityMatchingConfigObject.
    /// </summary>
    [BusinessDomain(BusinessDomain.OpenSource)]
    public interface IQualityMatchingService : IServiceBase
    {
        QualityDetail? DoMatching(ScriptableObject configObj, string deviceRatingKey);

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        QualityDetail? GetQualityDetail();

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        string GetQualityDetailKey();
    }

    public partial class FakeQualityMatchingService : IQualityMatchingService
    {
        public void OnStart()
        {
        }

        public void OnDestroy()
        {
#region GeneratedBreak
            Context.Break();
#endregion
        }

        public bool IsInited()
        {
            return false;
        }

        public bool IsImmortal()
        {
            return false;
        }

        public bool IsServiceInited()
        {
            throw new System.NotImplementedException();
        }

        public QualityDetail? DoMatching(ScriptableObject configObj, string deviceRatingKey)
        {
            return new QualityDetail();
        }

        public QualityDetail? GetQualityDetail()
        {
            return new QualityDetail();
        }

        public string GetQualityDetailKey()
        {
            return string.Empty;
        }
    }
}

```

## Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IQualityModifyService.cs

SHA256: d51c626dfc3345bce1db83ba591edd91e0ab6369f6c5d128880b2f15f4e8c564

```csharp
using UnityEngine;

namespace jj.Core.Runtime
{
    /// <summary>
    /// 画质参数实装（修改）服务，根据传入的画质参数修改显示效果。
    /// 当前运行设备匹配的画质参数通过<see cref="IQualityMatchingService"/>服务获得。
    /// <seealso cref="IQualityMatchingService"/>
    /// <seealso cref="IQualityMatchingService.GetQualityDetail">IQualityMatchingService.GetQualityDetail()</seealso>
    /// </summary>
    [BusinessDomain(BusinessDomain.OpenSource)]
    public interface IQualityModifyService : IServiceBase
    {
        /// <summary>
        /// 执行画质修改，接受画质参数作为输入，根据输入修改显示效果。
        /// 设备匹配的画质参数可以通过<see cref="IQualityMatchingService"/>服务的<see cref="IQualityMatchingService.GetQualityDetail"/>接口获得。
        /// <seealso cref="IQualityMatchingService.GetQualityDetail">IQualityMatchingService.GetQualityDetail()</seealso>
        /// <seealso cref="QualityDetail"/>
        /// </summary>
        /// <param name="qualityDetail">画质参数</param>
        /// <param name="handlers">额外的画质参数处理器，不定参数，可选</param>
        public void DoQualityModify(QualityDetail qualityDetail, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false);
        public void DoQualityModify(QualityDetail qualityDetail, ScriptableObject unityQualityConfig, ScriptableObject urpAssetConfig, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false);

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetQualityDetailName();
    }

    public partial class FakeQualityModifyService : IQualityModifyService
    {
        public void OnStart()
        {
        }

        public void OnDestroy()
        {

#region GeneratedBreak
            Context.Break();
#endregion
        }
        public bool IsInited ()
        {
            return false;
        }
        public bool IsImmortal()
        {
            return false;
        }

        public bool IsServiceInited ()
        {
            throw new System.NotImplementedException();
        }

        public void DoQualityModify(QualityDetail qualityDetail, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false)
        {
        }

        public void DoQualityModify(QualityDetail qualityDetail, ScriptableObject unityQualityConfig, ScriptableObject urpAssetConfig, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false)
        {
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetQualityDetailName()
        {
            return string.Empty;
        }
    }
}

```

## Assets/JJBifrost/bifrost/Runtime/Script/ExportApi/Core/APMServices/IQualityHandler.cs

SHA256: e1aab201db20e97ff0ff52dca3c64b3b514a9ba198ed7786931c3d963a0970a9

```csharp
namespace jj.Core.Runtime
{
    /// <summary>
    /// Applies the quality parameters defined by a <see cref="QualityDetail"/>.
    /// </summary>
    public interface IQualityHandler
    {
        public string ErrorCode { get; }
        public bool Handle(QualityDetail qualityDetail);
        public void Release();
    }

    public class FakeQualityHandler : IQualityHandler
    {
        public string ErrorCode => string.Empty;

        public bool Handle(QualityDetail qualityDetail)
        {
            return true;
        }

        public void Release()
        {
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/QualityMatchingService.cs

SHA256: 35d4e7108fb7c9bdc79b48a2a4322c00f26430aca23581d0ebfa9b5aae1c506a

```csharp
using System.Collections.Generic;
using jj.AOT.Runtime;
using UnityEngine;

namespace jj.Core.Runtime
{
    [InjectMethod(typeof(BootstrapSampler))]
    [ServiceInited]
    public partial class QualityMatchingService : IQualityMatchingService
    {
        private const string _TAG = "APM";

        private QualityDetail? _qualityDetail;
        private string _qualityDetailKey;

        public QualityMatchingConfigObject MatchingConfigObject { get; private set; }

        void OnConstructor()
        {
        }

        public void OnStart()
        {
            MarkServiceInited();
        }

        public void OnDestroy()
        {
            MarkServiceUnInited();
#region GeneratedBreak
            Context.Break();
#endregion
        }

        public bool IsImmortal()
        {
            return false;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public QualityDetail? GetQualityDetail()
        {
            return _qualityDetail;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetQualityDetailKey()
        {
            return _qualityDetailKey;
        }

        private QualityMatchingConfigObject GetMatchingConfig(ScriptableObject configObj)
        {
            MatchingConfigObject = configObj as QualityMatchingConfigObject;
            if (MatchingConfigObject == null)
            {
                if (JJLog.LogEnable)
                    JJLog.LogWarning(_TAG, "config object must be a QualityMatchingConfigObject.");
                return null;
            }

            if (MatchingConfigObject.deviceKey == null || MatchingConfigObject.configList == null ||
                MatchingConfigObject.deviceKey.Count == 0 ||
                MatchingConfigObject.deviceKey.Count != MatchingConfigObject.configList.Count)
            {
                if (JJLog.LogEnable)
                    JJLog.LogWarning(_TAG, "deviceKey and configList must be non-empty and have the same number of entries.");
                return null;
            }

            return MatchingConfigObject;
        }

        private (QualityDetail?, string) DoMatchingInternal(QualityMatchingConfigObject matchingConfig, string deviceRatingKey)
        {
            var detailIndex = matchingConfig.deviceKey.IndexOf(deviceRatingKey);
            if (detailIndex < 0)
            {
                if (JJLog.LogEnable)
                    JJLog.LogWarning(_TAG, $"cannot find matching quality detail for device({deviceRatingKey}).");
                return (null, string.Empty);
            }

            var configElements = matchingConfig.configList[detailIndex].list;
            var detailMap = new Dictionary<string, int>();
            if (configElements != null)
                for (var i = 0; i < configElements.Count; ++i)
                {
                    var element = configElements[i];
                    if (!string.IsNullOrEmpty(element.name) && !detailMap.ContainsKey(element.name))
                        detailMap.Add(element.name, element.value);
                }

            var detail = new QualityDetail { name = deviceRatingKey, detailMap = detailMap };
            return (detail, deviceRatingKey);
        }
        
        public QualityDetail? DoMatching(ScriptableObject configObj, string deviceRatingKey)
        {
            _qualityDetail = null;
            _qualityDetailKey = string.Empty;

            var config = GetMatchingConfig(configObj);
            if (config == null)
            {
                if (JJLog.LogEnable)
                    JJLog.LogWarning(_TAG, "config loading failed.");
                return null;
            }

            (_qualityDetail, _qualityDetailKey) = DoMatchingInternal(config, deviceRatingKey);

            return _qualityDetail;
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/QualityModifyService.cs

SHA256: 322b4036a1383bfa2769139af8163ce075e00cf4972b88fce7672a4327329a2e

```csharp
using jj.AOT.Runtime;
using UnityEngine;

namespace jj.Core.Runtime
{
    [InjectMethod(typeof(BootstrapSampler))]
    [ServiceInited]
    public partial class QualityModifyService : IQualityModifyService
    {
        private const string _TAG = "APM";
        private UnityQualityHandler _internalQualityHandler;
        private string _qualityDetailName = "";

        public void OnStart()
        {
            _internalQualityHandler = new UnityQualityHandler();
            MarkServiceInited();
        }

        public void OnDestroy()
        {
            MarkServiceUnInited();
#region GeneratedBreak
            Context.Break();
#endregion
            _internalQualityHandler?.Release();
            _internalQualityHandler = null;
#if UNITY_EDITOR
            ExternalHandler = null;
            InternalUnityQualityConfig = null;
            InternalURPAssetConfig = null;
#endif
        }

        public bool IsImmortal()
        {
            return false;
        }

        public void DoQualityModify(QualityDetail qualityDetail, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false)
        {
            DoQualityModify(qualityDetail, null, null, externalQualityHandler, banInternalHandler);
        }

        public void DoQualityModify(QualityDetail qualityDetail, ScriptableObject unityQualityConfig, ScriptableObject urpAssetConfig, IQualityHandler externalQualityHandler = null, bool banInternalHandler = false)
        {
            if (qualityDetail.detailMap == null)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, "quality detail map cannot be null.");
                }
                return;
            }

            if (unityQualityConfig != null && unityQualityConfig is not UnityQualitySettingsParameterConfig)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, "unityQualityConfig type wrong.");
                }
            }

            if (urpAssetConfig != null && urpAssetConfig is not URPAssetParameterConfig)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, "urpAssetConfig type wrong.");
                }
            }

            _internalQualityHandler.UnityQualityConfig = unityQualityConfig as UnityQualitySettingsParameterConfig;
            _internalQualityHandler.URPAssetConfig = urpAssetConfig as URPAssetParameterConfig;
#if UNITY_EDITOR
            ExternalHandler = externalQualityHandler;
            InternalUnityQualityConfig = unityQualityConfig as UnityQualitySettingsParameterConfig;
            InternalURPAssetConfig = urpAssetConfig as URPAssetParameterConfig;
#endif
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"modify quality with detail: {qualityDetail.name}.");
            }

            HandleQualityDetail(qualityDetail, banInternalHandler ? null : _internalQualityHandler, externalQualityHandler);
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetQualityDetailName()
        {
            return _qualityDetailName;
        }

        private void HandleQualityDetail(QualityDetail qualityDetail, IQualityHandler internalHandler, IQualityHandler externalHandler)
        {
            _qualityDetailName = qualityDetail.name;
            if (internalHandler != null && !internalHandler.Handle(qualityDetail))
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, $"error occurred during handling quality detail internal: \n{internalHandler.ErrorCode}");
                }
            }

            if (externalHandler != null && !externalHandler.Handle(qualityDetail))
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, $"error occurred during handling quality detail external: \n{externalHandler.ErrorCode}");
                }
            }
        }

#if UNITY_EDITOR
        public IQualityHandler ExternalHandler { get; set; }
        public UnityQualitySettingsParameterConfig InternalUnityQualityConfig { get; set; }
        public URPAssetParameterConfig InternalURPAssetConfig { get; set; }
#endif
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/DeviceRatingService.cs

SHA256: dc62ff98d6d4cb8981bff0e109945b10c6035fe9956077296193bc0a541f3d08

```csharp
using System;
#if WEIXINMINIGAME
using System.Text.RegularExpressions;
#endif
using System.Threading;
using Cysharp.Threading.Tasks;
using jj.AOT.Runtime;
using jj.Bifrost.Runtime;
using UnityEngine;
using UnityEngine.Assertions;

namespace jj.Core.Runtime
{
    [InjectMethod(typeof(BootstrapSampler))]
    [ConstructorInjector(typeof(IUserDefault))]
    [ConstructorInjector(typeof(ISystemInfoService))]
    [ConstructorInjector(typeof(IAssetLoader))]
    [ConstructorInjector(typeof(ITimeUtil))]
    [ConstructorInjector(typeof(ICryptoUtil))]
    [ConstructorInjector(typeof(IHttpRequestUtil))]
    [ServiceInited]
    public partial class DeviceRatingService : IDeviceRatingService
    {
        private const string _TAG = "APM";

        private int _ratingIdx = -1;
        private int _rating = -1;
        private string _ratingKey = "";

        private APMDefine.DeviceInfo? _deviceInfo;
        private DeviceScoreLocalProvider _localDeviceScoreProvider;
        private DeviceScoreRemoteProvider _remoteDeviceScoreProvider;
        private CancellationTokenSource _localScoreProviderCts;
        private CancellationTokenSource _remoteScoreProviderCts;

        public PlatformDeviceRatingConfig? RatingConfig { get; private set; }
        public DeviceRatingConfigObject RatingConfigObject { get; private set; }

        void OnConstructor ()
        {
        }

        public void OnStart()
        {
            MarkServiceInited();
            if (_localScoreProviderCts != null)
            {
                _localScoreProviderCts.Cancel();
                _localScoreProviderCts.Dispose();
            }
            _localScoreProviderCts = new CancellationTokenSource();
            if (_remoteScoreProviderCts != null)
            {
                _remoteScoreProviderCts.Cancel();
                _remoteScoreProviderCts.Dispose();
            }
            _remoteScoreProviderCts = new CancellationTokenSource();
            //提前触发获取设备分数
            CollectDeviceInfoAsync().Forget();
        }

        public void OnDestroy()
        {
            MarkServiceUnInited();
#region GeneratedBreak
            Context.Break();
#endregion
            Release();
        }

        public bool IsImmortal()
        {
            return false;
        }

        public async UniTask<int> DoRatingAsync(ScriptableObject configObj)
        {
            var config = GetRatingConfig(configObj);
            if (!TryPrepareRating(config))
                return _rating;

            if (ShouldRefreshDeviceInfo())
                _deviceInfo = await CollectDeviceInfoAsync();
            return CompleteRating(config.Value);
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetDeviceRating()
        {
            return _rating;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public string GetDeviceRatingKey()
        {
            return _ratingKey;
        }

        public int GetRemoteMatch()
        {
            if (UserDefault == null)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.Log("DeviceRatingService", "GetRemoteMatch UserDefault is null");
                }
                
                return APMDefine.PERFORMANCE_SCORE_CHECK_RESULT_NOT_MATCH;
            }
            
            if (JJLog.LogEnable)
            {
                JJLog.Log("DeviceRatingService", $"GetRemoteMatch Result {UserDefault.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_SCORE_CHECK_RESULT)}");
            }
            
            return UserDefault.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_SCORE_CHECK_RESULT, APMDefine.PERFORMANCE_SCORE_CHECK_RESULT_NOT_MATCH);
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public int GetIndex()
        {
            return _ratingIdx;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public APMDefine.DeviceInfo? GetDeviceInfo()
        {
            return _deviceInfo;
        }

        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.AggressiveInlining)]
        public void SetDeviceInfo(APMDefine.DeviceInfo deviceInfo)
        {
            // TODO 校验外部设置的DeviceInfo
            _deviceInfo = deviceInfo;
        }

        public void Release()
        {
            Context.Break();
            if (_localScoreProviderCts != null)
            {
                _localScoreProviderCts.Cancel();
                _localScoreProviderCts.Dispose();
                _localScoreProviderCts = null;
            }
            if (_remoteScoreProviderCts != null)
            {
                _remoteScoreProviderCts.Cancel();
                _remoteScoreProviderCts.Dispose();
                _remoteScoreProviderCts = null;
            }
            if (_localDeviceScoreProvider != null)
            {
                _localDeviceScoreProvider.Release();
                _localDeviceScoreProvider = null;
            }
            if (_remoteDeviceScoreProvider != null)
            {
                _remoteDeviceScoreProvider = null;
            }
        }

        private PlatformDeviceRatingConfig? GetRatingConfig(ScriptableObject configObj)
        {
            RatingConfigObject = configObj as DeviceRatingConfigObject;
            if (RatingConfigObject == null)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, "config object must be a DeviceRatingConfigObject.");
                }
                return null;
            }

            var config = RatingConfigObject.config;
            config.configname = configObj.name;
            var checker = new DeviceRatingConfigChecker(config);
            if (!checker.Check(out var error))
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, $"config checking meets some problems and may not working properly. \n{error}");
                }
            }

            return config;
        }

        private APMDefine.DeviceInfo CreateDeviceInfo()
        {
            var systemInfoService = Injector.Instance.CreateOrGetInstance<ISystemInfoService>();

            var deviceInfo = new APMDefine.DeviceInfo();
            // 从ISystemInfoService的接口返回值构建DeviceInfo
            deviceInfo.name = systemInfoService.DeviceInfo.DeviceName;
            //deviceInfo.model = systemInfoService.DeviceInfo.DeviceModel;
            deviceInfo.model = systemInfoService.DeviceInfo.RealDeviceModel;
#if !UNITY_EDITOR && (UNITY_ANDROID || UNITY_IOS)
            deviceInfo.soc = systemInfoService.HardwareInfo.ChipsetModel;
#else // UNITY_EDITOR || UNITY_STANDALONE_WIN || UNITY_STANDALONE_OSX
            deviceInfo.soc = systemInfoService.HardwareInfo.ProcessorType;
#endif
            deviceInfo.cpuFreq = systemInfoService.HardwareInfo.ProcessorFrequency;
            deviceInfo.cpuCores = systemInfoService.HardwareInfo.ProcessorCount;
            deviceInfo.manufacturer = systemInfoService.DeviceInfo.DeviceBrand;
            deviceInfo.ram = systemInfoService.HardwareInfo.SystemMemorySize;
            deviceInfo.imei = systemInfoService.DeviceInfo.IMEI;
            deviceInfo.cpu = systemInfoService.HardwareInfo.ProcessorType;
            deviceInfo.gpu = systemInfoService.HardwareInfo.GraphicsDeviceName;
            deviceInfo.gpuVendor = systemInfoService.HardwareInfo.GraphicsDeviceVendor;
            deviceInfo.gpuSeries = systemInfoService.HardwareInfo.GraphicsDeviceSeries;
            deviceInfo.gpuVendorId = systemInfoService.HardwareInfo.GraphicsDeviceVendorID;
            deviceInfo.gpuDeviceId = systemInfoService.HardwareInfo.GraphicsDeviceID;
            deviceInfo.gpuId = systemInfoService.HardwareInfo.GraphicsDeviceID;
            deviceInfo.os = systemInfoService.OperatingSystemInfo.OperatingSystem ?? String.Empty;
            deviceInfo.osVer = systemInfoService.OperatingSystemInfo.OperatingSystemVersion ?? String.Empty;
            deviceInfo.terminal = systemInfoService.DeviceInfo.Terminal;

            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"current device model is . {deviceInfo.model}");
            }

#if WEIXINMINIGAME
            if (string.IsNullOrEmpty(systemInfoService.HardwareInfo.ChipsetModel) == false)
            {
                deviceInfo.soc = systemInfoService.HardwareInfo.ChipsetModel;
            }
            deviceInfo.cpu = systemInfoService.HardwareInfo.ChipsetModel;

            //注意这里的兼容必须保留，因为现在走的是同步的getscore，同步的不等待服务器返回，就会第一次进游戏的时候，掉落到了default最低分
            bool isModelModified = false;
            // 处理形如 "iPhone 7 Plus<iPhone9,2>" 的特殊型号名，提取 < > 中的标准型号标识符
            var bracketStart = deviceInfo.model.IndexOf('<');
            var bracketEnd = deviceInfo.model.IndexOf('>');
            if (bracketStart >= 0 && bracketEnd > bracketStart)
            {
                deviceInfo.model = deviceInfo.model.Substring(bracketStart + 1, bracketEnd - bracketStart - 1);
                isModelModified = true;
            }
            if (isModelModified == false)
            {
                // 微信模拟器返回的是营销名（如 "iPhone 12/13 (Pro)"），转换为简化型号标识符（如 "iPhone12"）
                var modelMatch = Regex.Match(deviceInfo.model, @"^(iPhone|iPad)\s+(\d+)");
                if (modelMatch.Success)
                {
                    deviceInfo.model = modelMatch.Groups[1].Value + modelMatch.Groups[2].Value;
                }
            }
#endif
            return deviceInfo;
        }
        
        private async UniTask<APMDefine.DeviceInfo> CollectDeviceInfoAsync()
        {
            var deviceInfo = CreateDeviceInfo();
            var deviceScore = await GetDeviceScoreAsync(deviceInfo);
            ApplyDeviceScore(ref deviceInfo, deviceScore);

            return deviceInfo;
        }

        private void GetRemoteDeviceScore(APMDefine.DeviceInfo deviceInfo)
        {
            //已经发起了,不要重复发起
            if (_remoteDeviceScoreProvider != null)
            {
                return;
            }
            // 远端评分具有最高优先级，但不参与本次游戏拉起周期内的设备评级：
            // 远端评分系统存在时，向远端评分系统发送请求（遵照远端接口调用规则），待网络消息返回后如果评分数值有效则直接做持久化存储，留给下次游戏拉起时使用
            if (_remoteDeviceScoreProvider == null)
                _remoteDeviceScoreProvider = new DeviceScoreRemoteProvider();
            else
            {
                _remoteScoreProviderCts.Cancel();   // _remoteScoreProviderCts一旦cancel需要重新创建，否则cancel标记不会重置
                _remoteScoreProviderCts.Dispose();
                _remoteScoreProviderCts = new CancellationTokenSource();
            }
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, "request device score via remote score provider.");
            }
            _remoteDeviceScoreProvider.GetScoreAsync(deviceInfo, _remoteScoreProviderCts.Token)
                .ContinueWith(StoreRemoteDeviceScore).Forget();
        }

        private async UniTask<DeviceScore> GetDeviceScoreAsync(APMDefine.DeviceInfo deviceInfo)
        {
            // 评分默认优先取用本地持久化存储的数值
            var score = GetDeviceScoreLocal();
            
            //发起一次远端分数刷新
            GetRemoteDeviceScore(deviceInfo);
            
            // 如果没有找到本地持久化存储，需要寻求本地评分系统：
            // 本地评分系统存在时，采用本地评分配置对设备进行评分，如果评分数值有效（大于0）则取用该数值，同时将该数值做持久化存储
            if (!score.IsValid())
            {
                if (_localDeviceScoreProvider == null)
                    _localDeviceScoreProvider = new DeviceScoreLocalProvider();
                var localScore = await _localDeviceScoreProvider.GetScoreAsync(deviceInfo, _localScoreProviderCts.Token);
                if (JJLog.LogEnable)
                {
                    JJLog.Log(_TAG, $"get device score via local score provider. {localScore}");
                }
                if (localScore.IsValid())
                {
                    score = StoreDeviceScoreLocal(localScore);
                }
            }
            
            if (score.IsValid())
            {
                return score;
            }
            // 无法获取到有效评分数值，就取用预定义评分数值（通常是3000，代码中定义常量）
            return GetRealDeviceScoreOrDefault();
        }

        public DeviceScore GetDeviceScoreLocal()
        {
            return new DeviceScore(UserDefault?.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_SCORE, 0) ?? 0,
                UserDefault?.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_CPU_SCORE, 0) ?? 0,
                UserDefault?.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_GPU_SCORE, 0) ?? 0);
        }

        private DeviceScore GetRealDeviceScoreOrDefault()
        {
            var score = GetDeviceScoreLocal();
            if (score.IsValid())
                return score;

            score = new DeviceScore(APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE,
                APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE, APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE);
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"use default device score. {score}");
            }
            return score;
        }

        private static void ApplyDeviceScore(ref APMDefine.DeviceInfo deviceInfo, DeviceScore deviceScore)
        {
            deviceInfo.score = deviceScore.MobileScore;
            deviceInfo.cpuScore = deviceScore.CPUScore;
            deviceInfo.gpuScore = deviceScore.GPUScore;
        }

        private DeviceScore StoreDeviceScoreLocal(DeviceScore score)
        {
#if WEIXINMINIGAME
            score = AdjustWeixinIosScoreIfNeeded(score);
#endif
            if (score.IsValid())
            {
                UserDefault?.SetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_SCORE, score.MobileScore);
                UserDefault?.SetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_CPU_SCORE, score.CPUScore);
                UserDefault?.SetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_GPU_SCORE, score.GPUScore);
                if (JJLog.LogEnable)
                {
                    JJLog.Log(_TAG, $"store device score: {score}.");
                }
            }
            return score;
        }

        private void StoreRemoteDeviceScore(DeviceScore score)
        {
            if (score.IsValid() == false)
            {
                return;
            }
            
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"get device score via remote score provider. {score}");
            }
            
//editor环境远端返回的分数不要，为了保证editor都是最高画质
#if UNITY_EDITOR
            score = new DeviceScore(APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE, APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE, APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE);
#endif
            score = StoreDeviceScoreLocal(score);
        }

        private (int, string, int) DoRatingInternal(PlatformDeviceRatingConfig ratingConfig, APMDefine.DeviceInfo deviceInfo)
        {
            var ratingIdx = ratingConfig.defaultrating;
            Assert.IsTrue(ratingIdx >= 0);

            // 模拟器的情况下直接返回专属档位
            if (IsEmulator())
            {
                ratingIdx = ratingConfig.emulatorrating;
                Assert.IsTrue(ratingIdx >= 0);
                if (JJLog.LogEnable)
                {
                    JJLog.Log(_TAG, $"rating as emulator: {ratingIdx}");
                }
                return (ratingConfig.ratingids[ratingIdx], ratingConfig.ratingkeys[ratingIdx], ratingIdx);
            }

            // 优先判定白名单，白名单命中就直接返回判定结果
            var tempIdx = -1;
            var filterOptions = ratingConfig.filteroptions;
            if (filterOptions > 0)
                tempIdx = RatingByFilters(ratingConfig, deviceInfo);
            if (tempIdx >= 0)
            {
                ratingIdx = tempIdx;
                if (JJLog.LogEnable)
                {
                    JJLog.Log(_TAG, $"rating by filters: {ratingIdx}");
                }
                return (ratingConfig.ratingids[ratingIdx], ratingConfig.ratingkeys[ratingIdx], ratingIdx);
            }

            // 白名单未命中才判定阈值
            var thresholdOptions = ratingConfig.thresholdoptions;
            if (thresholdOptions > 0)
                tempIdx = RatingByThresholds(ratingConfig, deviceInfo);
            if (tempIdx >= 0)
            {
                ratingIdx = tempIdx;
                if (JJLog.LogEnable)
                {
                    JJLog.Log(_TAG, $"rating by thresholds: {ratingIdx}");
                }
                return (ratingConfig.ratingids[ratingIdx], ratingConfig.ratingkeys[ratingIdx], ratingIdx);
            }

            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"rating as default: {ratingIdx}");
            }
            return (ratingConfig.ratingids[ratingIdx], ratingConfig.ratingkeys[ratingIdx], ratingIdx);
        }

        private bool IsEmulator()
        {
            return SystemInfoService.DeviceInfo.IsSimulator;
        }

        // 白名单匹配
        private int RatingByFilters(PlatformDeviceRatingConfig config, APMDefine.DeviceInfo deviceInfo)
        {
            // 白名单匹配遵循短路原则，按照 设备型号>>>GPU型号>>>SOC型号>>>产商 的优先级序列顺次进行匹配，一旦成功匹配立刻跳出序列。
            // 各个类型白名单的设备等级计算结果取值范围为 [0 ~ 最大等级定义-1]，匹配失败时返回 -1。
            var rating = -1;

            var useRegex = config.regex > 0;
            if (HasFilters(config.filteroptions, FilterOption.Combine))
            {
                rating = RatingByCombineFilters(config.filtercombine, deviceInfo, useRegex);
            }
            if (rating < 0 && HasFilters(config.filteroptions, FilterOption.Model))
            {
                rating = RatingByFilters(config.filtermodel, deviceInfo.model, useRegex);
            }

            if (rating < 0 && HasFilters(config.filteroptions, FilterOption.GPU))
            {
                rating = RatingByFilters(config.filtergpu, deviceInfo.gpu, useRegex);
            }

            if (rating < 0 && HasFilters(config.filteroptions, FilterOption.SOC))
            {
                rating = RatingByFilters(config.filtersoc, deviceInfo.soc, useRegex);
            }

            if (rating < 0 && HasFilters(config.filteroptions, FilterOption.Manu))
            {
                rating = RatingByFilters(config.filtermanu, deviceInfo.manufacturer, useRegex);
            }

            return rating;
        }

        // 阈值匹配
        private int RatingByThresholds(PlatformDeviceRatingConfig config, APMDefine.DeviceInfo deviceInfo)
        {
            // 阈值匹配遵循水桶原则，所有类型的阈值中计算出来的设备等级取最低值。
            // 各个种类阈值的设备等级计算结果取值范围为 [0 ~ 最大等级定义-1]，计算失败（条件不足）时返回 int.MaxValue。
            // 最终计算结果如果依旧为int.MaxValue，说明阈值匹配失败，将返回 -1。
            var rating = int.MaxValue;

            if (HasThresholds(config.thresholdoptions, ThresholdOption.Score) && deviceInfo.score > 0)
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdscores, deviceInfo.score));
            }
            if (HasThresholds(config.thresholdoptions, ThresholdOption.CPUScores) && deviceInfo.cpuScore > 0)
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdcpuscores, deviceInfo.cpuScore));
            }
            if (HasThresholds(config.thresholdoptions, ThresholdOption.GPUScores) && deviceInfo.gpuScore > 0)
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdgpuscores, deviceInfo.gpuScore));
            }
            if (HasThresholds(config.thresholdoptions, ThresholdOption.OSVer) && deviceInfo.osVer.Length > 0)
            {
                rating = Math.Min(rating, RatingByVersionThresholds(config.thresholdosver, deviceInfo.osVer));
            }

#if WEIXINMINIGAME
            var weChatBenchmarkScore = GetWeChatBenchmarkScoreLocal();
            if (HasThresholds(config.thresholdoptions, ThresholdOption.WeChatBenchmark) && weChatBenchmarkScore > 0)
            {
                var wxRating = RatingByThreshold(config.thresholdwechatbenchmarks, weChatBenchmarkScore);
                rating = Math.Min(rating, wxRating);
                //如果是使用的默认分数，且微信分级有分数的情况下，使用微信分级的结果，防止最新的高端机没分数的情况下，显示低端效果
                if (deviceInfo.cpuScore == APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE
                    && deviceInfo.gpuScore == APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE
                    && deviceInfo.score == APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE)
                {
                    rating = wxRating;
                }
            }
#endif

            if (HasThresholds(config.thresholdoptions, ThresholdOption.Resolution))
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdresolution, deviceInfo.resWidth));
            }

            if (HasThresholds(config.thresholdoptions, ThresholdOption.RAM))
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdram, deviceInfo.ram));
            }

            if (HasThresholds(config.thresholdoptions, ThresholdOption.CPUFreq))
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdcpufreq, deviceInfo.cpuFreq));
            }

            if (HasThresholds(config.thresholdoptions, ThresholdOption.CPUCores))
            {
                rating = Math.Min(rating, RatingByThreshold(config.thresholdcpucores, deviceInfo.cpuCores));
            }

            if (HasThresholds(config.thresholdoptions, ThresholdOption.GPUVendor))
            {
                rating = Math.Min(rating,
                    RatingByGPUVendorThresholds(config.thresholdgpuvendor, deviceInfo.gpuVendor, deviceInfo.gpuSeries, deviceInfo.gpuId));
            }

            return rating == int.MaxValue ? -1 : rating;
        }

#if WEIXINMINIGAME
        private int GetWeChatBenchmarkScoreLocal()
        {
            return UserDefault?.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_WECHAT_BENCHMARK_SCORE, 0) ?? 0;
        }
#endif

        public static bool HasFilters(int options, FilterOption option)
        {
            return (options & 1 << (int)(option)) > 0;
        }

        public static bool HasThresholds(int options, ThresholdOption option)
        {
            return (options & (1 << (int)option)) > 0;
        }

        private int RatingByFilters(StringArrayWrapper[] filterConditions, string value, bool regex)
        {
            Assert.IsNotNull(filterConditions);

            var rating = -1;
            for (var i = 0; i < filterConditions.Length; ++i)
            {
                var subConditions = filterConditions[i];
                foreach (var cond in subConditions.values)
                {
                    // TODO 支持正则匹配
                    if (value.StartsWith(value))
                    {
                        rating = i;
                        break;
                    }
                }
            }

            return rating;
        }

        private static string NormalizeVersionString(string version)
        {
            if (string.IsNullOrWhiteSpace(version))
                return string.Empty;

            version = version.Trim();
            // 微信 system 形如 "iOS 26.5" / "Android 12"，去掉 OS 名称前缀
            var spaceIdx = version.IndexOf(' ');
            if (spaceIdx >= 0 && spaceIdx < version.Length - 1)
            {
                var afterSpace = version.Substring(spaceIdx + 1).Trim();
                if (afterSpace.Length > 0 && char.IsDigit(afterSpace[0]))
                    return afterSpace;
            }

            // 无空格时从首个数字起截取（兼容异常格式）
            for (var i = 0; i < version.Length; i++)
            {
                if (char.IsDigit(version[i]))
                    return version.Substring(i);
            }

            return version;
        }

        private static int ParseVersionPart(string part)
        {
            if (string.IsNullOrEmpty(part))
                return 0;

            var end = 0;
            while (end < part.Length && char.IsDigit(part[end]))
                end++;
            if (end > 0 && int.TryParse(part.AsSpan(0, end), out var leadingNumber))
                return leadingNumber;

            return int.TryParse(part, out var value) ? value : 0;
        }

        private static int VerionCompare(string ver1, string ver2)
        {
            ver1 = NormalizeVersionString(ver1);
            ver2 = NormalizeVersionString(ver2);

            var v1Parts = ver1.Split('.');
            var v2Parts = ver2.Split('.');
            var maxLength = Math.Max(v1Parts.Length, v2Parts.Length);

            for (var i = 0; i < maxLength; i++)
            {
                var v1 = i < v1Parts.Length ? ParseVersionPart(v1Parts[i]) : 0;
                var v2 = i < v2Parts.Length ? ParseVersionPart(v2Parts[i]) : 0;

                if (v1 > v2)
                    return 1;
                if (v1 < v2)
                    return -1;
            }

            return 0;
        }

#if WEIXINMINIGAME
        private const string WEIXIN_IOS_MIN_OS_VER = "16.0.0";

        private DeviceScore AdjustWeixinIosScoreIfNeeded(DeviceScore score)
        {
            if (!score.IsValid())
                return score;

            var terminal = SystemInfoService?.DeviceInfo.Terminal;
            if (!string.Equals(terminal, "ios", StringComparison.OrdinalIgnoreCase))
                return score;

            var osVer = SystemInfoService?.OperatingSystemInfo.OperatingSystemVersion ?? string.Empty;
            if (string.IsNullOrEmpty(osVer) || VerionCompare(osVer, WEIXIN_IOS_MIN_OS_VER) >= 0)
                return score;

            if (score.MobileScore > 0)
                score.MobileScore = Mathf.RoundToInt(score.MobileScore * 0.5f);

            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"weixin ios osVer {osVer} < {WEIXIN_IOS_MIN_OS_VER}, device score halved: {score}");
            }
            return score;
        }
#endif

        private int RatingByCombineFilters(ArrayWrapper<FilterCombine>[] configFiltercombine, APMDefine.DeviceInfo deviceInfo, bool useRegex = false)
        {
            var rating = -1;
            for (var i = 0; i < configFiltercombine.Length; ++i)
            {
                var subConditions = configFiltercombine[i];
                foreach (var cond in subConditions.values)
                {
                    // TODO 支持正则匹配
                    var cpuName = cond.cpuName;
                    var gpuName = cond.gpuName;
                    var vendorId = cond.vendorId;
                    var deviceId = cond.deviceId;
                    var ram = cond.ram;
                    var os = cond.os;
                    var osVer = cond.osVer;

                    if (!string.IsNullOrEmpty(cpuName) && !deviceInfo.cpu.StartsWith(cpuName))
                    {
                        break;
                    }
                    if (!string.IsNullOrEmpty(gpuName) && !deviceInfo.gpu.StartsWith(gpuName))
                    {
                        break;
                    }
                    if (!string.IsNullOrEmpty(os) && !deviceInfo.os.StartsWith(os))
                    {
                        break;
                    }

                    if (!string.IsNullOrEmpty(osVer) && VerionCompare(deviceInfo.osVer, osVer) < 0)
                    {
                        break;
                    }
                    if (vendorId > 0 && vendorId != deviceInfo.gpuVendorId)
                    {
                        break;
                    }
                    if (deviceId > 0 && deviceId != deviceInfo.gpuDeviceId)
                    {
                        break;
                    }
                    if (ram > 0 && deviceInfo.ram < ram)
                    {
                        break;
                    }
                    rating = i;
                    break;
                }
            }

            return rating;
        }

        private int RatingByThreshold(int[] thresholds, int value, bool asc = true)
        {
            Assert.IsNotNull(thresholds);

            // 数值与阈值相同时的处理方案：当参数数值与某一档阈值相同时，一概算作下一档
            var rating = thresholds.Length > 0 ? 0 : int.MaxValue;
            for (var i = 0; i < thresholds.Length; ++i)
            {
                if (asc)
                {
                    if (thresholds[i] > value)
                        break;
                }
                else
                {
                    if (thresholds[i] < value)
                        break;
                }

                ++rating;
            }

            return rating;
        }

        private int RatingByVersionThresholds(string[] thresholds, string value, bool asc = true)
        {
            Assert.IsNotNull(thresholds);

            // 数值与阈值相同时的处理方案：当参数数值与某一档阈值相同时，一概算作下一档
            var rating = thresholds.Length > 0 ? 0 : int.MaxValue;
            for (var i = 0; i < thresholds.Length; ++i)
            {
                if (asc)
                {
                    if (VerionCompare(thresholds[i], value) > 0)
                        break;
                }
                else
                {
                    if (VerionCompare(thresholds[i], value) < 0)
                        break;
                }

                ++rating;
            }

            return rating;
        }

        private int RatingByGPUVendorThresholds(GPUVendor[] thresholds, string gpuVendor, string gpuSeries, int gpuId)
        {
            Assert.IsNotNull(thresholds);

            var rating = int.MaxValue;
            foreach (var vendor in thresholds)
            {
                if (!vendor.vendor.Equals(gpuVendor))
                    continue;
                foreach (var series in vendor.series)
                {
                    if (!series.name.Equals(gpuSeries))
                        continue;
                    rating = series.thresholds.Length > 0 ? 0 : int.MaxValue;
                    for (var i = 0; i < series.thresholds.Length; ++i)
                    {
                        if (series.thresholds[i] > gpuId)
                            break;
                        ++rating;
                    }

                    break;
                }

                break;
            }

            return rating;
        }
        
        private bool ShouldRefreshDeviceInfo()
        {
            if (_deviceInfo == null)
                return true;

            var localScore = GetDeviceScoreLocal();
            return (localScore.MobileScore > 0 && localScore.MobileScore != _deviceInfo.Value.score) ||
                   (localScore.CPUScore > 0 && localScore.CPUScore != _deviceInfo.Value.cpuScore) ||
                   (localScore.GPUScore > 0 && localScore.GPUScore != _deviceInfo.Value.gpuScore);
        }

        private bool TryPrepareRating(PlatformDeviceRatingConfig? config)
        {
            _rating = -1;
            _ratingKey = string.Empty;
            _ratingIdx = -1;

            RatingConfig = config;
            if (config == null)
            {
                if (JJLog.LogEnable)
                {
                    JJLog.LogWarning(_TAG, "config loading failed.");
                }
                return false;
            }

            return true;
        }

        private int CompleteRating(PlatformDeviceRatingConfig config)
        {
            Assert.IsTrue(_deviceInfo != null);
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG,
                    $"do rating with config {config.configname} " +
                    $" score:{_deviceInfo.Value.score} cpuScore:{_deviceInfo.Value.cpuScore} gpuScore:{_deviceInfo.Value.gpuScore}");
            }
            (_rating, _ratingKey, _ratingIdx) = DoRatingInternal(config, _deviceInfo.Value);
            if (JJLog.LogEnable)
            {
                JJLog.Log(_TAG, $"doRating _rating:{_rating} _ratingKey:{_ratingKey} _ratingIdx:{_ratingIdx}");
            }

            if (_rating > 0)
                UserDefault?.SetIntegerForKey(APMDefine.USER_DEFAULT_KEY_DEVICE_RATING, _rating);

            return _rating;
        }

        public int DoRating(ScriptableObject configObj)
        {
            var config = GetRatingConfig(configObj);
            if (!TryPrepareRating(config))
                return _rating;

            if (ShouldRefreshDeviceInfo())
            {
                var deviceInfo = CreateDeviceInfo();
                var deviceScore = GetRealDeviceScoreOrDefault();
                ApplyDeviceScore(ref deviceInfo, deviceScore);
                _deviceInfo = deviceInfo;
            }
            return CompleteRating(config.Value);
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/Modules/UnityQualityHandler.cs

SHA256: 0aaa65ba8728730d5da9ca9c0f7e7e6a36e52af21ec2ef1d7502863a56f90ae0

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading;
using jj.AOT.Runtime;
using jj.Bifrost.Runtime;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace jj.Core.Runtime
{
    public class UnityQualityHandler : IQualityHandler
    {
        protected delegate bool OperatorFunctionDelegate(int value, out string err);

        public string ErrorCode { get; private set; } = string.Empty;
        public UnityQualitySettingsParameterConfig UnityQualityConfig {
            set
            {
                if (_unityQualityConfig == null)
                    _unityQualityConfig = new WeakReference<UnityQualitySettingsParameterConfig>(value);
                else
                    _unityQualityConfig.SetTarget(value);
            }
        }
        private WeakReference<UnityQualitySettingsParameterConfig> _unityQualityConfig;
        public URPAssetParameterConfig URPAssetConfig {
            set
            {
                if (_urpAssetConfig == null)
                    _urpAssetConfig = new WeakReference<URPAssetParameterConfig>(value);
                else
                    _urpAssetConfig.SetTarget(value);
            }
        }
        private WeakReference<URPAssetParameterConfig> _urpAssetConfig;

        protected readonly Dictionary<string, OperatorFunctionDelegate> operatorLut;

        private readonly StringBuilder _internalErrorCache = new();
        // private Dictionary<int, List<WeakReference<PostProcessData>>> _originalPostProcessDataLut;
        private CancellationTokenSource _cts = new();

        private int _maximumResolutionHeight = -1;
        private int _maximumResolutionWidth = -1;
        private float _screenRatio = -1f;

        public UnityQualityHandler()
        {
            var resolutionSupports = Screen.resolutions;
            foreach (var res in resolutionSupports)
            {
#if UNITY_ANDROID || UNITY_IOS
                // 对于移动设备横竖屏变化的情况，这里定义Width是分辨率宽高中较大的那个数值
                _maximumResolutionWidth = Math.Max(_maximumResolutionWidth, Math.Max(res.width, res.height));
                _maximumResolutionHeight = Math.Max(_maximumResolutionHeight, Math.Min(res.width, res.height));
#else
                _maximumResolutionWidth = Math.Max(_maximumResolutionWidth, res.width);
                _maximumResolutionHeight = Math.Max(_maximumResolutionHeight, res.height);
#endif
            }

            _screenRatio = _maximumResolutionWidth / (float) _maximumResolutionHeight;

            // 不要依赖OpFunc的定义顺序，这里应该是无序执行的
            operatorLut = new Dictionary<string, OperatorFunctionDelegate>
            {
                ["shader_lod"] = HandleShaderLOD,
                ["shader_quality"] = HandleShaderQuality,
                ["unity_quality"] = HandleUnityQuality, // 与unity_quality_param不可共存
                ["unity_quality_param"] = HandleUnityQualityParam,  // 与unity_quality不可共存
                ["urp_asset"] = HandleUrpAsset, // 与urp_param不可共存
                ["urp_param"] = HandleUrpAssetParam,    // 与urp_asset不可共存
                // ["post_processing"] = HandlePostProcessing,  // 不再单独处理post_processing，它跟随管线参数设置
                ["msaa"] = HandleMSAA,
                ["post_aa"] = HandlePostAA,
                ["screen_resolution"] = HandleScreenResolution,
                ["low_model_character"] = HandleLowModelCharacter,
            };
        }

        public virtual void Release()
        {
            _internalErrorCache.Clear();

            // if (_originalPostProcessDataLut != null && _originalPostProcessDataLut.Count > 0)
            // {
            //     var curPipelineAsset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            //     if (curPipelineAsset != null)
            //         RestoreURPPostProcessData(curPipelineAsset);
            //     _originalPostProcessDataLut.Clear();
            //     _originalPostProcessDataLut = null;
            // }

            UnityQualityConfig = null;
            URPAssetConfig = null;

            _cts.Cancel();
            _cts.Dispose();
        }

        public bool Handle(QualityDetail qualityDetail)
        {
            if (qualityDetail.detailMap == null)
                return false;

            // 设置全局默认ShaderLOD，在Handler生效前设置，Handler可覆盖此数值
            var userDefault = Injector.Instance.CreateOrGetInstance<IUserDefault>();
            var score = userDefault.GetIntegerForKey(APMDefine.USER_DEFAULT_KEY_PERFORMANCE_SCORE, APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE);
            if (score <= 0)
                score = APMDefine.DEFAULT_DEVICE_PERFORMANCE_SCORE;
            if (score > 100)
                Shader.globalMaximumLOD = score / 100 * 10;
            else
                Shader.globalMaximumLOD = 1;
            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Set default globalMaximumLOD {Shader.globalMaximumLOD}");
            // 设置全局默认Shader质量（默认高），Handler可覆盖此设置
            Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_LOW);
            Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_MID);
            Shader.EnableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_HIGH);
            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Set default Keyword {APMDefine.KEYWORDS_SHADER_QUALITY_HIGH}");

            _internalErrorCache.Clear();
            var hasError = false;
            foreach (var kv in operatorLut)
            {
                if (!qualityDetail.detailMap.TryGetValue(kv.Key, out var value))
                    continue;
                var opFunc = kv.Value;
                if (opFunc == null)
                {
                    hasError = true;
                    _internalErrorCache.AppendLine($"operator for {kv.Key} is null.");
                    continue;
                }

                if (!opFunc(value, out var err))
                {
                    hasError = true;
                    _internalErrorCache.AppendLine(err);
                }
            }

            if (_cts.IsCancellationRequested)
            {
                return false;
            }

            ErrorCode = _internalErrorCache.ToString();
            return !hasError;
        }

        protected void AddHandleFunction(string key, OperatorFunctionDelegate opFunc)
        {
            operatorLut[key] = opFunc;
        }

        private bool HandleShaderLOD(int value, out string error)
        {
            error = string.Empty;

            if (value <= 0)
            {
                error = "shader lod cannot less than 1";
                return false;
            }

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Set globalMaximumLOD {value}");
            Shader.globalMaximumLOD = value;
            return true;
        }

        private bool HandleShaderQuality(int value, out string error)
        {
            error = string.Empty;

            if (value < 0)
            {
                error = "shader quality cannot less than 0";
                return false;
            }

            switch (value)
            {
                case 0:// 低
                    Shader.EnableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_LOW);
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_MID);
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_HIGH);
                    if (JJLog.LogEnable)
                        JJLog.Log("APM", $"Set Keyword {APMDefine.KEYWORDS_SHADER_QUALITY_LOW}");
                    break;
                case 1:// 中
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_LOW);
                    Shader.EnableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_MID);
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_HIGH);
                    if (JJLog.LogEnable)
                        JJLog.Log("APM", $"Set Keyword {APMDefine.KEYWORDS_SHADER_QUALITY_MID}");
                    break;
                case 2:// 高
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_LOW);
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_MID);
                    Shader.EnableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_HIGH);
                    if (JJLog.LogEnable)
                        JJLog.Log("APM", $"Set Keyword {APMDefine.KEYWORDS_SHADER_QUALITY_HIGH}");
                    break;
                default:// 默认高
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_LOW);
                    Shader.DisableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_MID);
                    Shader.EnableKeyword(APMDefine.KEYWORDS_SHADER_QUALITY_HIGH);
                    if (JJLog.LogEnable)
                        JJLog.Log("APM", $"Set Keyword {APMDefine.KEYWORDS_SHADER_QUALITY_HIGH}");
                    break;
            }
            return true;
        }

        private bool HandleUnityQuality(int value, out string error)
        {
            error = string.Empty;

            var total = QualitySettings.count;
            if (value < 0 || value >= total)
            {
                error = $"unity quality level value invalid, supported range is [0-{total}]";
                return false;
            }

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Set QualitySettings {value}");
            QualitySettings.SetQualityLevel(value);
            return true;
        }

        private bool HandleUnityQualityParam(int value, out string error)
        {
            error = string.Empty;

            if (_unityQualityConfig == null || !_unityQualityConfig.TryGetTarget(out var unityQualityConfig) || unityQualityConfig.allLevels == null)
            {
                error = "unity quality config missing";
                return false;
            }

            if (value >= unityQualityConfig.allLevels.Length)
            {
                error = "input parameter out of range";
                return false;
            }

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Copy QualitySettings {value}");
            unityQualityConfig.allLevels[value].Apply();
            return true;
        }

        private bool HandleUrpAsset(int value, out string error)
        {
            error = string.Empty;

            if (_urpAssetConfig == null || !_urpAssetConfig.TryGetTarget(out var urpAssetConfig) || urpAssetConfig.allUrpAssets == null)
            {
                error = "urp quality config missing";
                return false;
            }

            if (value >= urpAssetConfig.allUrpAssets.Length)
            {
                error = "input parameter out of range";
                return false;
            }

            var urpAsset = urpAssetConfig.allUrpAssets[value];
            if (urpAsset == null)
            {
                error = "urp asset in config is null";
                return false;
            }

            if (urpAsset != GraphicsSettings.defaultRenderPipeline)
            {
                var oldAsset = GraphicsSettings.defaultRenderPipeline;
                GraphicsSettings.defaultRenderPipeline = urpAsset;
                // if (oldAsset as UniversalRenderPipelineAsset != null)
                //     RestoreURPPostProcessData((UniversalRenderPipelineAsset) oldAsset);
                if (JJLog.LogEnable)
                    JJLog.Log("APM", $"Change RenderPipelineAsset:{urpAsset.name} <<< {(oldAsset != null ? oldAsset.name : "none")}");
            }

            // 如果clone存在，说明不是首次应用此urpAsset，存在其参数已经被修改的可能，需要把clone上的参数复制过来覆盖此urpAsset
            // 如果clone不存在，说明首次应用此urpAsset，创建clone作为此urpAsset原始参数的备份
            if (urpAssetConfig.allUrpAssetClones[value] != null)
                CopyRenderPipelineAssetParams(urpAsset, urpAssetConfig.allUrpAssetClones[value], true);
            else
                urpAssetConfig.CreateClone(value);

            if(QualitySettings.renderPipeline != null)
                QualitySettings.renderPipeline = null;  // 清理QualitySettings里设置的urpAsset，理论上不支持QualitySettings里设置urpAsset
            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Use urp asset: {urpAsset.name}");

            var curPipelineAsset = GraphicsSettings.currentRenderPipeline as UniversalRenderPipelineAsset;
            if (curPipelineAsset != urpAsset)
            {
                if (JJLog.LogEnable)
                    JJLog.LogWarning("APM", $"Something wrong! currentRenderPipeline is not defaultRenderPipeline");
            }

            // RecordURPPostProcessData(urpAsset as UniversalRenderPipelineAsset);

            return true;
        }

        private bool HandleUrpAssetParam(int value, out string error)
        {
            error = string.Empty;

            if (_urpAssetConfig == null || !_urpAssetConfig.TryGetTarget(out var urpAssetConfig) || urpAssetConfig.allUrpAssets == null)
            {
                error = "urp quality config missing";
                return false;
            }

            if (value >= urpAssetConfig.allUrpAssets.Length)
            {
                error = "input parameter out of range";
                return false;
            }

            var urpAsset = GraphicsSettings.currentRenderPipeline;// as UniversalRenderPipelineAsset;
            if (urpAsset != null)
            {
                // RecordURPPostProcessData(urpAsset as UniversalRenderPipelineAsset);

                // urpAssetConfig.allLevels[value].Apply(urpAsset);
                CopyRenderPipelineAssetParams(urpAsset, urpAssetConfig.allUrpAssets[value], false);
            }

            return true;
        }

        // private bool HandlePostProcessing(int value, out string error)
        // {
        //     error = string.Empty;
        //
        //     // var mainCamera = Camera.main;
        //     // if (mainCamera == null)
        //     // {
        //     //     error = "main camera missing";
        //     //     return false;
        //     // }
        //     //
        //     // var cameraData = mainCamera.GetComponent<UniversalAdditionalCameraData>();
        //     // if (cameraData == null)
        //     // {
        //     //     error = "camera data missing";
        //     //     return false;
        //     // }
        //     //
        //     // cameraData.renderPostProcessing = value > 0;
        //     //
        //     // var volume = mainCamera.GetComponent<Volume>();
        //     // if (volume != null)
        //     //     volume.enabled = value > 0;
        //
        //     // 象棋后处理使用的特殊性，后处理跟特效走，所以需要从更根源的地方来处理后处理功能启停。
        //     //
        //     var curPipelineAsset = GraphicsSettings.currentRenderPipeline;
        //     if (curPipelineAsset == null)
        //     {
        //         // TODO 兼容Builtin管线下使用UnityPostProcessingV2的情况
        //         error = "scriptable render pipeline missing";
        //         return false;
        //     }
        //
        //     if (curPipelineAsset is UniversalRenderPipelineAsset urpPipelineAsset)
        //     {
        //         // 最后尝试一次记录修改前的PostProcessData，此处仅当urp_asset和urp_param两个Handler都未激活时才会满足
        //         if(_originalPostProcessDataLut == null || !_originalPostProcessDataLut.ContainsKey(urpPipelineAsset.GetInstanceID()))
        //             RecordURPPostProcessData(urpPipelineAsset);
        //
        //         if (value > 0)
        //             RestoreURPPostProcessData(urpPipelineAsset);
        //         else
        //             ClearURPPostProcessData(urpPipelineAsset);
        //
        //         // Temp: HDR和PostProcessing统一开启和关闭，移动平台目前不开后处理的情况下开启HDR没有任何作用，反而产生额外的RenderPass
        //         HandleHDR(value, out error);
        //     }
        //
        //     return true;
        // }

        // private bool HandleHDR(int value, out string error)
        // {
        //     error = string.Empty;
        //     var renderPipelineAsset = GraphicsSettings.currentRenderPipeline;
        //     if (renderPipelineAsset != null)
        //     {
        //         // is using SRP
        //         if (renderPipelineAsset is UniversalRenderPipelineAsset urpAsset)
        //         {
        //             // only support urp for now
        //             urpAsset.supportsHDR = value > 0;
        //         }
        //         // TODO support other customised SRP
        //     }
        //     else
        //     {
        //         // is using builtin
        //         // TODO support builtin??
        //     }
        //
        //     return true;
        // }

        private bool HandleMSAA(int value, out string error)
        {
            error = string.Empty;
            var renderPipelineAsset = GraphicsSettings.currentRenderPipeline;
            if (renderPipelineAsset != null)
            {
                // is using SRP
                if (renderPipelineAsset is UniversalRenderPipelineAsset urpAsset)
                {
                    // only support urp for now
                    urpAsset.msaaSampleCount = value >= 2 ? value : 1; // urp的msaa以1表示禁用，其余与builtin相同，所以这里需要特别转换一下
                }
                // TODO support other customised SRP
            }
            else
            {
                // is using builtin
                QualitySettings.antiAliasing = value;
            }

            return true;
        }

        private bool HandlePostAA(int value, out string error)
        {
            error = string.Empty;
            var renderPipelineAsset = GraphicsSettings.defaultRenderPipeline;
            if (renderPipelineAsset != null && renderPipelineAsset is UniversalRenderPipelineAsset)
            {
                var mainCamera = Camera.main;
                if (mainCamera != null)
                {
                    var additionalData = mainCamera.GetUniversalAdditionalCameraData();
                    additionalData.antialiasing = (AntialiasingMode) value;
                }
            }

            return true;
        }

        private bool HandleScreenResolution(int value, out string error)
        {
            error = string.Empty;

            if (value < 0 || value > _maximumResolutionHeight)
            {
                error = $"resolution value invalid, supported range is [0-{_maximumResolutionHeight}].";
                return false;
            }

            Screen.SetResolution(Mathf.RoundToInt(value * _screenRatio), value, false);//Screen.fullScreen);
            return true;
        }

        private bool HandleLowModelCharacter(int value, out string error)
        {
            error = string.Empty;

            if (value < 0 || value > 1)
            {
                error = $"low_model_character value invalid, supported range is [0-1].";
                return false;
            }

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Set {APMDefine.KEYWORDS_LOW_CHARACTER_QUALITY}:{(value > 0 ? "enable" : "disable")}");

            if(value > 0)
                Shader.EnableKeyword(APMDefine.KEYWORDS_LOW_CHARACTER_QUALITY);
            else
                Shader.DisableKeyword(APMDefine.KEYWORDS_LOW_CHARACTER_QUALITY);

            return true;
        }

        // private void RecordURPPostProcessData(UniversalRenderPipelineAsset curPipelineAsset)
        // {
        //     if (curPipelineAsset == null)
        //         return;
        //     _originalPostProcessDataLut ??= new Dictionary<int, List<WeakReference<PostProcessData>>>();
        //     if (!_originalPostProcessDataLut.TryGetValue(curPipelineAsset.GetInstanceID(), out var postDataRefList))
        //     {
        //         postDataRefList = new List<WeakReference<PostProcessData>>();
        //         _originalPostProcessDataLut.Add(curPipelineAsset.GetInstanceID(), postDataRefList);
        //     }
        //     postDataRefList.Clear(); // 每次记录urpAsset上的postProcessData都是重新记录，如果其他地方修改了这项数据，这里记录可能会出现差错，理论上不允许其他地方修改
        //     var rendererDataList = curPipelineAsset.m_RendererDataList;
        //     var count = rendererDataList.Length;
        //     for (var i = 0; i < count; ++i)
        //     {
        //         var urData = rendererDataList[i] as UniversalRendererData;
        //         postDataRefList.Add(new WeakReference<PostProcessData>(urData == null ? null : urData.postProcessData));
        //     }
        // }

        // private void ClearURPPostProcessData(UniversalRenderPipelineAsset curPipelineAsset)
        // {
        //     var dataList = curPipelineAsset.m_RendererDataList;
        //     var count = dataList.Length;
        //     for (var i = 0; i < count; ++i)
        //     {
        //         var urData = dataList[i] as UniversalRendererData;
        //         if (urData == null || urData.postProcessData == null)
        //             continue;
        //         urData.postProcessData = null;
        //         urData.SetDirty();
        //     }
        // }

        // private void RestoreURPPostProcessData(UniversalRenderPipelineAsset curPipelineAsset)
        // {
        //     if(_originalPostProcessDataLut == null || curPipelineAsset == null)
        //         return;
        //     if (!_originalPostProcessDataLut.TryGetValue(curPipelineAsset.GetInstanceID(), out var postDataRefList))
        //         return;
        //     var dataList = curPipelineAsset.m_RendererDataList;
        //     var count = Math.Min(dataList.Length, postDataRefList.Count);
        //     for (var i = 0; i < count; ++i)
        //     {
        //         var urData = dataList[i] as UniversalRendererData;
        //         if (urData == null)
        //             continue;
        //         postDataRefList[i].TryGetTarget(out var postData);
        //         urData.postProcessData = postData;
        //         urData.SetDirty();
        //     }
        // }

        private void CopyRenderPipelineAssetParams(RenderPipelineAsset dest, RenderPipelineAsset src, bool removeUnexpectedFeature)
        {
            if (JJLog.LogEnable)
                JJLog.Log("APM", $"Copy RenderPipelineAsset parameters:{src.name} >>> {dest.name}");
            if (dest is UniversalRenderPipelineAsset universeDest && src is UniversalRenderPipelineAsset universeSrc)
            {
                CopyUniversalRenderPipelineAssetParams(universeDest, universeSrc, removeUnexpectedFeature);
            }
            else if (dest is ICompatibleRenderPipelineAsset compatibleDest)
            {
                compatibleDest.CopyAssetParamsFrom(src, removeUnexpectedFeature);
            }
            else if (src is ICompatibleRenderPipelineAsset compatibleSrc)
            {
                compatibleSrc.CopyAssetParamsTo(dest, removeUnexpectedFeature);
            }
        }

        private void CopyUniversalRenderPipelineAssetParams(UniversalRenderPipelineAsset dest, UniversalRenderPipelineAsset src, bool removeUnexpectedFeature)
        {
            if(src == null || dest == null)
                return;

            // copy pipelineAsset参数
            dest.supportsCameraDepthTexture = src.supportsCameraDepthTexture;
            dest.supportsCameraOpaqueTexture = src.supportsCameraOpaqueTexture;
            dest.opaqueDownsampling = src.opaqueDownsampling;
            dest.useSRPBatcher = src.useSRPBatcher;
            dest.supportsDynamicBatching = src.supportsDynamicBatching;
            dest.enableEmptyCameraOptimize = src.enableEmptyCameraOptimize;
            dest.supportsHDR = src.supportsHDR;
            dest.msaaSampleCount = src.msaaSampleCount;
            dest.renderScale = src.renderScale;
            dest.mainLightRenderingMode = src.mainLightRenderingMode;
            dest.supportsMainLightShadows = src.supportsMainLightShadows;
            dest.mainLightShadowmapResolution = src.mainLightShadowmapResolution;
            dest.additionalLightsRenderingMode = src.additionalLightsRenderingMode;
            dest.maxAdditionalLightsCount = src.maxAdditionalLightsCount;
            dest.supportsAdditionalLightShadows = src.supportsAdditionalLightShadows;
            dest.additionalLightsShadowmapResolution = src.additionalLightsShadowmapResolution;
            dest.shadowDistance = src.shadowDistance;
            dest.shadowCascadeCount = src.shadowCascadeCount;
            dest.cascade2Split = src.cascade2Split;
            dest.cascade3Split = src.cascade3Split;
            dest.cascade4Split = src.cascade4Split;
            dest.cascadeBorder = src.cascadeBorder;
            dest.shadowDepthBias = src.shadowDepthBias;
            dest.shadowNormalBias = src.shadowNormalBias;
            dest.supportsSoftShadows = src.supportsSoftShadows;
            dest.conservativeEnclosingSphere = src.conservativeEnclosingSphere;

            // TODO copy rendererData参数

            // 暂时只支持单一rendererData的情况
            var destRendererData = dest.m_RendererDataList[0];
            var srcRendererData = src.m_RendererDataList[0];
            CopyUniversalRenderPipelineAssetRendererFeatures(destRendererData, srcRendererData, removeUnexpectedFeature, out var needReload);
            if (needReload)
                destRendererData.SetDirty();
        }

        private void CopyUniversalRenderPipelineAssetRendererFeatures(ScriptableRendererData dest, ScriptableRendererData src, bool removeUnexpected, out bool needReload)
        {
            needReload = false;
            if(src == null || dest == null)
                return;

            // copy rendererFeature参数
            var srcFeatureCopiedIdxSet = new HashSet<int>();
            var removeList = new List<ScriptableRendererFeature>();
            for (var i = 0; i < dest.rendererFeatures.Count; ++i)
            {
                var destRendererFeature = dest.rendererFeatures[i];
                if (destRendererFeature == null)
                    continue;
                var destType = destRendererFeature.GetType();
                var copied = false;
                for (var ii = 0; ii < src.rendererFeatures.Count; ++ii)
                {
                    if (srcFeatureCopiedIdxSet.Contains(ii))
                        continue;
                    var srcRendererFeature = src.rendererFeatures[ii];
                    if (srcRendererFeature == null)
                        continue;
                    if (destType == srcRendererFeature.GetType())
                    {
                        // 目前只支持ICompatibleRendererFeature之间复制参数
                        if (destRendererFeature is ICompatibleRendererFeature compFeature)
                            compFeature.CopySettingsFrom(srcRendererFeature);
                        srcFeatureCopiedIdxSet.Add(ii);
                        copied = true;
                    }
                }
                // 处理dest里存在额外RendererFeature的情况（需要移除dest里额外的RendererFeature）
                if (!copied && removeUnexpected)
                    removeList.Add(destRendererFeature);
            }
            // 额外Feature不能直接设置Active，而需要从Feature列表中移除。因为直接设置Active会修改feature来源管线asset，从而影响下次feature的copy
            if (removeList.Count > 0)
            {
                foreach (var feature in removeList)
                {
                    dest.rendererFeatures.Remove(feature);
                    feature.Dispose();
                }
                needReload = true;
            }

            // 处理src里有额外RendererFeature的情况（需要往dest里添加RendererFeature）
            if (srcFeatureCopiedIdxSet.Count < src.rendererFeatures.Count)
            {
                // copy rendererFeature
                for (var ii = 0; ii < src.rendererFeatures.Count; ++ii)
                {
                    if(srcFeatureCopiedIdxSet.Contains(ii))
                        continue;
                    var srcRendererFeature = src.rendererFeatures[ii];
                    dest.rendererFeatures.Add(srcRendererFeature);
                }
                needReload = true;
            }
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/Modules/DeviceQualityMatchOverrider.cs

SHA256: 340beef4e902ad357e495e48482a5e14ed035759492dbc5e58cbcdac6ff8376c

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using jj.AOT.Runtime;
using jj.Bifrost.Runtime;
using UnityEngine;

namespace jj.Core.Runtime
{
    public class DeviceQualityMatchOverrider : IDeviceQualityMatchOverrider
    {
        public int? RatingValue { get; private set; }
        public string RatingKey { get; private set; }
        public QualityDetail? QualityDetail { get; private set; }
        public APMDefine.DeviceInfo? DeviceInfo { get; private set; }

        public DeviceQualityMatchOverrideOption OverrideOptions { get; set; } = DeviceQualityMatchOverrideOption.None;

        public ScriptableObject DeviceRatingConfig
        {
            get => GetReferenceTarget(_deviceRatingConfig);
            set => _deviceRatingConfig.SetTarget(value);
        }

        public ScriptableObject QualityMatchingConfig
        {
            get => GetReferenceTarget(_qualityMatchingConfig);
            set => _qualityMatchingConfig.SetTarget(value);
        }

        public ScriptableObject UnityQualityConfig
        {
            get => GetReferenceTarget(_unityQualityConfig);
            set => _unityQualityConfig.SetTarget(value);
        }

        public ScriptableObject URPAssetConfig
        {
            get => GetReferenceTarget(_urpAssetConfig);
            set => _urpAssetConfig.SetTarget(value);
        }

        public IQualityHandler QualityHandler
        {
            get => GetReferenceTarget(_extraQualityHandler);
            set => _extraQualityHandler.SetTarget(value);
        }

        public Action<IDeviceQualityMatchOverrider> OnOverriderApplied { get; set; }
        public Action<IDeviceQualityMatchOverrider> OnOverriderLifted { get; set; }

        internal bool IsBaseOverrider { get; set; } = false;
        private QualityDetail _baseQualityDetail; // BaseOverrider特有的调整版QualityDetail

        private readonly WeakReference<ScriptableObject> _deviceRatingConfig = new(null);
        private readonly WeakReference<ScriptableObject> _qualityMatchingConfig = new(null);
        private readonly WeakReference<ScriptableObject> _unityQualityConfig = new(null);
        private readonly WeakReference<ScriptableObject> _urpAssetConfig = new(null);

        private readonly WeakReference<IDeviceRatingService> _deviceRatingService = new((IDeviceRatingService) Injector.Instance.QueryInstance(typeof(IDeviceRatingService)));
        private readonly WeakReference<IQualityMatchingService> _qualityMatchingService = new((IQualityMatchingService) Injector.Instance.QueryInstance(typeof(IQualityMatchingService)));
        private readonly WeakReference<IQualityModifyService> _qualityModifyService = new((IQualityModifyService) Injector.Instance.QueryInstance(typeof(IQualityModifyService)));
        private readonly WeakReference<IAppPerfManageService> _appPerfManageService = new((IAppPerfManageService) Injector.Instance.QueryInstance(typeof(IAppPerfManageService)));

        private readonly WeakReference<IQualityHandler> _extraQualityHandler = new(null);

        public string Name { get; set; }

        // 兼容性目的，在棋牌项目还没有完全迁移到统一分级标准前，任何游戏项目启动修改画质前都先将管线和画质恢复到通用的Base状态
        // 公共模块figure和tkmatch不需要执行恢复到Base的操作
        private bool NeedRestoreQuality => !IsBaseOverrider && !_excludeList.Contains(Name);
        private readonly HashSet<string> _excludeList = new() { "figure", "tkmatch" };

        internal DeviceQualityMatchOverrider(string name)
        {
            Name = name;
        }

        public override string ToString()
        {
            return Name;
        }

        public void Release()
        {
            _appPerfManageService.TryGetTarget(out var appPerfManageService);
            appPerfManageService?.ReturnDeviceQualityMatchOverrider(this);
        }

        public void CalculateDeviceRatingAndQualityMatching()
        {
            ApplyDeviceRating();
            ApplyQualityMatching();
        }

        public void OverrideQualityModify()
        {
            // 兼容性目的，在棋牌项目还没有完全迁移到统一分级标准前，任何游戏项目启动修改画质前都先将管线和画质恢复到通用的Base状态
            if (NeedRestoreQuality)
            {
                _appPerfManageService.TryGetTarget(out var appPerfManageService);
                appPerfManageService?.RestoreDeviceQualityMatch();
            }

            var hasOverride = ApplyQualityModify();
            if(hasOverride)
                OnOverriderApplied?.Invoke(this);
        }

        public void LiftOverride()
        {
            OnOverriderLifted?.Invoke(this);
        }

        public void Reset()
        {
            RatingValue = null;
            RatingKey = null;
            QualityDetail = null;
            DeviceInfo = null;

            _deviceRatingConfig.SetTarget(null);
            _qualityMatchingConfig.SetTarget(null);
            _unityQualityConfig.SetTarget(null);
            _urpAssetConfig.SetTarget(null);

            _extraQualityHandler.SetTarget(null);
        }

        private void ApplyDeviceRating()
        {
            if (JJLog.LogEnable)
                JJLog.Log("APM", $"ApplyDeviceRating {Name}");
            if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.OverrideDeviceRatingConfig))
            {
                _deviceRatingService.TryGetTarget(out var deviceRatingService);
                // 开始执行设备分级
                deviceRatingService?.DoRating(DeviceRatingConfig);
                // 从设备分级服务接口获取设备分级关键字
                RatingValue = deviceRatingService?.GetDeviceRating();
                RatingKey = deviceRatingService?.GetDeviceRatingKey();
                DeviceInfo = deviceRatingService?.GetDeviceInfo();
            }
            else
            {
                _appPerfManageService.TryGetTarget(out var appPerfManageService);
                RatingValue = appPerfManageService?.RatingValue;
                RatingKey = appPerfManageService?.RatingKey;
                DeviceInfo = appPerfManageService?.DeviceInfo;
            }
        }

        private void ApplyQualityMatching()
        {
            // 如果没有RatingKey，需要先执行DeviceRating
            if (RatingKey == null)
                ApplyDeviceRating();

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"ApplyQualityMatching {Name}");
            _qualityMatchingService.TryGetTarget(out var qualityMatchingService);
            if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.OverrideQualityMatchingConfig))
            {
                // 开始执行画质适配
                qualityMatchingService?.DoMatching(QualityMatchingConfig, RatingKey);
                // 从画质适配服务获取适配后的画质参数
                QualityDetail = qualityMatchingService?.GetQualityDetail();
            }
            else if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.AdditionalQualityMatchingConfig))
            {
                // 开始执行画质适配
                qualityMatchingService?.DoMatching(QualityMatchingConfig, RatingKey);
                // 从画质适配服务获取适配后的画质参数
                QualityDetail = qualityMatchingService?.GetQualityDetail();
                // 从AppPerfManageService获取通用分级的QualityDetail
                _appPerfManageService.TryGetTarget(out var appPerfManageService);
                var commonQualityDetail = appPerfManageService?.QualityDetail;
                // 把commonQualityDetail合并到QualityDetail里去
                QualityDetail = MergeQualityDetail(commonQualityDetail, QualityDetail/*, key => key.Equals("urp_asset") ? "urp_param" : key*/);
            }
            else
            {
                _appPerfManageService.TryGetTarget(out var appPerfManageService);
                QualityDetail = appPerfManageService?.QualityDetail;
            }

            // 针对BaseOverrider调整QualityDetail内容
            if (QualityDetail != null && IsBaseOverrider)
            {   // BaseOverrider里需把urp_param替换为urp_asset，也就是BaseOverrider必然替换管线，但其他Overrider在复用QualityDetail时依然使用urp_param覆盖管线参数
                _baseQualityDetail = QualityDetail.Value;
                _baseQualityDetail.detailMap = new Dictionary<string, int>(QualityDetail.Value.detailMap);
                if (_baseQualityDetail.detailMap.TryGetValue("urp_param", out var value))
                {
                    _baseQualityDetail.detailMap["urp_asset"] = value;
                    _baseQualityDetail.detailMap.Remove("urp_param");
                }
            }
        }

        private bool ApplyQualityModify()
        {
            // 如果没有QualityDetail，需要先执行QualityMatching
            if (QualityDetail == null)
                ApplyQualityMatching();

            if (QualityDetail == null)
            {
                JJLog.LogError("APM", "QualityDetail is null");
                return false;
            }

            if (JJLog.LogEnable)
                JJLog.Log("APM", $"ApplyQualityModify {Name}");
            _appPerfManageService.TryGetTarget(out var appPerfManageService);
            var unityQualityConfig = ((AppPerfManageService)appPerfManageService)?.UnityQualityConfig;
            var urpAssetConfig = ((AppPerfManageService)appPerfManageService)?.URPAssetConfig;
            var hasOverride = false;
            if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.OverrideUnityQualityConfig))
            {
                unityQualityConfig = UnityQualityConfig;
                hasOverride = true;
            }

            if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.OverrideURPAssetConfig))
            {
                urpAssetConfig = URPAssetConfig;
                hasOverride = true;
            }

            // 使用qualityDetail时区分BaseOverrider和普通Overrider
            var qualityDetail = IsBaseOverrider ? _baseQualityDetail : QualityDetail.Value;

            _qualityModifyService.TryGetTarget(out var qualityModifyService);
            if (OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.OverrideQualityHandler))
            {
                // 开始执行画质参数应用
                qualityModifyService?.DoQualityModify(qualityDetail, unityQualityConfig, urpAssetConfig, QualityHandler, true);
                hasOverride = true;
            }
            else if(OverrideOptions.HasFlag(DeviceQualityMatchOverrideOption.AdditionalQualityHandler))
            {
                // 开始执行画质参数应用
                qualityModifyService?.DoQualityModify(qualityDetail, unityQualityConfig, urpAssetConfig, QualityHandler);
                hasOverride = true;
            }
            else
            {
                // 开始执行画质参数应用
                qualityModifyService?.DoQualityModify(qualityDetail, unityQualityConfig, urpAssetConfig);
            }

            return hasOverride;
        }

        private static T GetReferenceTarget<T>(WeakReference<T> reference) where T : class
        {
            T config = null;
            reference?.TryGetTarget(out config);
            return config;
        }

        // 合并两个QualityDetail，name取qd2的，detailMap中如果存在相同key，将以qd2中的value覆盖
        private static QualityDetail MergeQualityDetail(QualityDetail? qd1, QualityDetail? qd2, Func<string, string> detailKeyReplacer = null)
        {
            var result = new QualityDetail();
            result.name = qd2 != null ? qd2.Value.name : qd1?.name;
            result.detailMap = new Dictionary<string, int>();
            CheckAddDetailMapItem(result.detailMap, qd1?.detailMap, detailKeyReplacer);
            CheckAddDetailMapItem(result.detailMap, qd2?.detailMap, detailKeyReplacer);

            if (JJLog.LogEnable)
            {
                var sb = new StringBuilder();
                foreach (var kv in result.detailMap)
                {
                    sb.Append(kv.Key);
                    sb.Append(':');
                    sb.Append(kv.Value);
                    sb.Append(',');
                }
                JJLog.Log("APM", $"MergeQualityDetail:{sb}");
            }
            return result;
        }

        private static void CheckAddDetailMapItem(Dictionary<string, int> destMap, Dictionary<string, int> srcMap, Func<string, string> detailKeyReplacer)
        {
            if (srcMap == null || destMap == null)
                return;
            foreach (var kv in srcMap)
            {
                var key = detailKeyReplacer != null ? detailKeyReplacer(kv.Key) : kv.Key;
                switch (key)
                {
                    case "urp_asset":
                        destMap.Remove("urp_param");
                        break;
                    case "urp_param":
                        destMap.Remove("urp_asset");
                        break;
                    case "unity_quality":
                        destMap.Remove("unity_quality_param");
                        break;
                    case "unity_quality_param":
                        destMap.Remove("unity_quality");
                        break;
                }
                destMap[key] = kv.Value;
            }
        }
    }
}
```

## Assets/JJCore/core/Runtime/Script/APMServices/Config/QualityMatchingConfigObject.cs

SHA256: 5c72bbc1db1c208f8ef1dbcd4da3fc5deea2db4b41f142ace904950086838ef6

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

namespace jj.Core.Runtime
{
    [CreateAssetMenu(fileName = "QualityMatchingConfig", menuName = "Game Setting Assets/Quality Matching Config Asset")]
    public class QualityMatchingConfigObject : ScriptableObject
    {
        public List<string> deviceKey;
        public List<ConfigList> configList;

        [Serializable]
        public struct ConfigList
        {
            public List<ConfigElement> list;
        }

        [Serializable]
        public struct ConfigElement
        {
            public string name;
            public int value;
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/Config/DeviceRatingConfigObject.cs

SHA256: bd7e0e282d57413d90d18eb2ee78f99bbb9d15bf33fab5c3d9b8b443de19d9db

```csharp
using UnityEngine;

namespace jj.Core.Runtime
{
    [CreateAssetMenu(fileName = "DeviceRatingConfig", menuName = "Game Setting Assets/Device Rating Config Asset")]
    public class DeviceRatingConfigObject : ScriptableObject
    {
        [SerializeField]
        public PlatformDeviceRatingConfig config;
    }
}
```

## Assets/JJCore/core/Runtime/Script/APMServices/Config/DeviceRatingConfig.cs

SHA256: 3b22ed6aeca347229370c6ec362ef4656f79f0d8b19ed35c98915c7a68dc0f8d

```csharp
using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Serialization;

namespace jj.Core.Runtime
{
    public enum FilterOption : int
    {
        Model = 0,
        GPU = 1,
        SOC = 2,
        Manu = 3,
        Combine = 4
    }

    public enum ThresholdOption
    {
        Resolution = 0,
        RAM = 1,
        CPUFreq = 2,
        CPUCores = 3,
        GPUVendor = 4,
        Score = 5,
        CPUScores = 6,
        GPUScores = 7,
        OSVer = 8,
        WeChatBenchmark = 9
    }

    [Serializable]
    public class StringArrayWrapper
    {
        public string[] values;

        public StringArrayWrapper(string[] values)
        {
            this.values = values;
        }

        public StringArrayWrapper()
        {
            this.values = Array.Empty<string>();
        }
    }

    [Serializable]
    public class ArrayWrapper<T>
    {
        public T[] values;
    }

    [Serializable]
    public struct FilterCombine
    {
        public string cpuName;
        public string gpuName;
        public int vendorId;
        public int deviceId;
        public int ram;
        public string os;
        public string osVer;
    }
    
    [Serializable]
    public struct PlatformDeviceRatingConfig
    {
        public int version;
        public string configname;
        public string platform;
        public int totalrating;
        public int[] ratingids;
        public string[] ratingkeys;
        public int defaultrating;
        public int emulatorrating;
        public int regex;
        
        public int filteroptions;
        public ArrayWrapper<FilterCombine>[] filtercombine;
        public StringArrayWrapper[] filtermodel;
        public StringArrayWrapper[] filtergpu;
        public StringArrayWrapper[] filtersoc;
        public StringArrayWrapper[] filtermanu;
        
        public int thresholdoptions;
        public int[] thresholdresolution;
        public int[] thresholdram;
        public int[] thresholdcpufreq;
        public int[] thresholdcpucores;
        public GPUVendor[] thresholdgpuvendor;
        public int[] thresholdscores;
        public int[] thresholdcpuscores;
        public int[] thresholdgpuscores;

        [Header("等于阈值时属于更低的级别")]
        public string[] thresholdosver;

        public int[] thresholdwechatbenchmarks;
    }

    [Serializable]
    public struct GPUVendor
    {
        public string vendor;
        public GPUSeries[] series;
    }

    [Serializable]
    public struct GPUSeries
    {
        public string name;
        public int[] thresholds;
    }

    public class DeviceRatingConfigChecker
    {
        public PlatformDeviceRatingConfig Config { get; }

        public DeviceRatingConfigChecker(PlatformDeviceRatingConfig config)
        {
            Config = config;
        }

        public bool Check(out string error)
        {
            var hasError = false;
            var sb = new StringBuilder();

            if (Config.ratingkeys == null || Config.ratingkeys.Length < Config.totalrating)
            {
                hasError = true;
                sb.Append("ratingkeys missing or mismatch\n");
            }

            if (Config.ratingids == null || Config.ratingids.Length < Config.totalrating)
            {
                hasError = true;
                sb.Append("ratingids missing or mismatch\n");
            }
            else
            {
                var lastId = -1;
                foreach (var id in Config.ratingids)
                {
                    if (id < 0)
                    {
                        hasError = true;
                        sb.Append("ratingids contains negative value\n");
                        break;
                    }

                    if (id <= lastId)
                    {
                        hasError = true;
                        sb.Append("ratingids must order by ASC\n");
                        break;
                    }

                    lastId = id;
                }
            }

            if (Config.defaultrating < 0 || Config.defaultrating > Config.totalrating)
            {
                hasError = true;
                sb.Append("defaultrating invalid\n");
            }

            if (Config.emulatorrating < 0 || Config.emulatorrating > Config.totalrating)
            {
                hasError = true;
                sb.Append("emulatorrating invalid\n");
            }

            var filterDimension = Config.totalrating;

            if ((Config.filteroptions & (1 << 0)) > 0 && Config.filtermodel.Length < filterDimension)
            {
                hasError = true;
                sb.Append("filtermodel\n");
            }

            if ((Config.filteroptions & (1 << 1)) > 0 && Config.filtergpu.Length < filterDimension)
            {
                hasError = true;
                sb.Append("filtergpu\n");
            }

            if ((Config.filteroptions & (1 << 2)) > 0 && Config.filtersoc.Length < filterDimension)
            {
                hasError = true;
                sb.Append("filtersoc\n");
            }

            if ((Config.filteroptions & (1 << 3)) > 0 && Config.filtermanu.Length < filterDimension)
            {
                hasError = true;
                sb.Append("filtermanu\n");
            }

            var thresholdDimension = Math.Max(0, Config.totalrating - 1);

            if ((Config.thresholdoptions & (1 << 0)) > 0 && Config.thresholdresolution.Length < thresholdDimension)
            {
                hasError = true;
                sb.Append("thresholdresolution\n");
            }

            if ((Config.thresholdoptions & (1 << 1)) > 0 && Config.thresholdram.Length < thresholdDimension)
            {
                hasError = true;
                sb.Append("thresholdram\n");
            }

            if ((Config.thresholdoptions & (1 << 2)) > 0 && Config.thresholdcpufreq.Length < thresholdDimension)
            {
                hasError = true;
                sb.Append("thresholdcpufreq\n");
            }

            if ((Config.thresholdoptions & (1 << 3)) > 0 && Config.thresholdcpucores.Length < thresholdDimension)
            {
                hasError = true;
                sb.Append("thresholdcpucores\n");
            }

            if ((Config.thresholdoptions & (1 << 4)) > 0)
            {
                foreach (var vendor in Config.thresholdgpuvendor)
                foreach (var series in vendor.series)
                {
                    if (series.thresholds.Length < thresholdDimension)
                    {
                        hasError = true;
                        sb.Append($"thresholdgpuvendor {vendor.vendor} {series.name} \n");
                    }
                }
            }

            if ((Config.thresholdoptions & (1 << 5)) > 0 && Config.thresholdscores.Length < thresholdDimension)
            {
                hasError = true;
                sb.Append("thresholdscores\n");
            }

            if ((Config.thresholdoptions & (1 << 9)) > 0 &&
                (Config.thresholdwechatbenchmarks == null || Config.thresholdwechatbenchmarks.Length < thresholdDimension))
            {
                hasError = true;
                sb.Append("thresholdwechatbenchmarks\n");
            }

            error = sb.Length > 0 ? sb.ToString() : null;

            return !hasError;
        }
    }
}

```

## Assets/JJCore/core/Runtime/Script/APMServices/Config/UnityQualitySettingsParameterConfig.cs

SHA256: eb1299c8f3f4d3f1aab97537c9eadcec0aa92f1f2e3baab9843b36f33e012699

```csharp
using UnityEngine;

namespace jj.Core.Runtime
{
    [CreateAssetMenu(fileName = "UnityQualitySettings", menuName = "Game Setting Assets/Unity QualitySettings Asset")]
    public class UnityQualitySettingsParameterConfig : ScriptableObject
    {
        public UnityQualitySettingsParameter[] allLevels;
    }
}
```

## Assets/JJCore/core/Runtime/Script/APMServices/Config/URPAssetParameterConfig.cs

SHA256: fe5e108a42d3a087fbd36ea5201401b60fbd2562e21fb0929e9bcdc3648da599

```csharp
using System;
using jj.Bifrost.Runtime;
using UnityEngine;
using UnityEngine.Assertions;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

namespace jj.Core.Runtime
{
    [CreateAssetMenu(fileName = "URPQualitySettings", menuName = "Game Setting Assets/URP Parameter Asset")]
    public class URPAssetParameterConfig : ScriptableObject
    {
        [Obsolete("Use allUrpAssets instead", true)]
        [HideInInspector]
        public URPAssetParameter[] allLevels;

        public RenderPipelineAsset[] allUrpAssets;

        [NonSerialized]
        public RenderPipelineAsset[] allUrpAssetClones;

        private void Awake()
        {
            allUrpAssetClones = new RenderPipelineAsset[allUrpAssets.Length];
        }

        private void OnDestroy()
        {
            for (var i = 0; i < allUrpAssetClones.Length; ++i)
            {
                var rpAssetClone = allUrpAssetClones[i];
                if (rpAssetClone is UniversalRenderPipelineAsset urpAssetClone)
                {
                    for (var ii = 0; ii < urpAssetClone.m_RendererDataList.Length; ++ii)
                    {
                        var rendererDataClone = urpAssetClone.m_RendererDataList[ii];
                        for (var iii = 0; iii < rendererDataClone.rendererFeatures.Count; ++iii)
                        {
                            var featureClone = rendererDataClone.rendererFeatures[iii];
                            Destroy(featureClone);
                        }
                        Destroy(rendererDataClone);
                    }
                }
                else if (rpAssetClone is ICompatibleRenderPipelineAsset compAssetClone)
                {
                    // 处理定制管线
                    for (var ii = 0; ii < compAssetClone.RendererFeatures.Count; ++ii)
                    {
                        var featureClone = compAssetClone.RendererFeatures[ii];
                        Destroy(featureClone);
                    }
                }
                Destroy(rpAssetClone);
            }
        }

        public RenderPipelineAsset CreateClone(int idx)
        {
            Assert.IsTrue(idx >= 0 && idx < allUrpAssets.Length);
            var rpAsset = allUrpAssets[idx];
            if (rpAsset == null)
                return null;
            var rpAssetClone = Instantiate(rpAsset);
            if (rpAsset is UniversalRenderPipelineAsset urpAsset && rpAssetClone is UniversalRenderPipelineAsset urpAssetClone)
            {
                var dataCount = urpAsset.m_RendererDataList.Length;
                for (var i = 0; i < dataCount; ++i)
                {
                    var rendererData = urpAsset.m_RendererDataList[i];
                    var rendererDataClone = Instantiate(rendererData);
                    var featureCount = rendererData.rendererFeatures.Count;
                    for (var j = 0; j < featureCount; ++j)
                    {
                        var feature = rendererData.rendererFeatures[j];
                        var featureClone = Instantiate(feature);
                        rendererDataClone.rendererFeatures[j] = featureClone;
                    }
                    urpAssetClone.m_RendererDataList[i] = rendererDataClone;
                }
            }
            else if (rpAsset is ICompatibleRenderPipelineAsset compAsset && rpAssetClone is ICompatibleRenderPipelineAsset compAssetClone)
            {
                // 处理定制管线
                var featureCount = compAsset.RendererFeatures.Count;
                for (var i = 0; i < featureCount; ++i)
                {
                    var feature = compAsset.RendererFeatures[i];
                    var featureClone = Instantiate(feature);
                    compAssetClone.RendererFeatures[i] = featureClone;
                }
            }
            allUrpAssetClones[idx] = rpAssetClone;
            return rpAssetClone;
        }
    }
}
```

## Assets/JJCore/core/Tests/Runtime/Script/APMServices/UTQualityMatchingService.cs

SHA256: e902b61f953c276623cf21af98602b0b4e87cb7d13a004adba5d71cc1685af88

```csharp
using System.Collections.Generic;
using System.Text.RegularExpressions;
using jj.Core.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace jj.Core.Tests.Runtime
{
    [TestFixture]
    [Category("APM_QualityMatchingService")]
    public class UTQualityMatchingService
    {
        private IQualityMatchingService _qualityMatchingService;

        [OneTimeSetUp]
        public void SetUp()
        {
            var injector = new ServiceInjector();
            injector.RegisterSelf();
            injector.Register<IQualityMatchingService, QualityMatchingService>();
            injector.Register<ILogService, LogService>();
            _qualityMatchingService = injector.CreateOrGetInstance<IQualityMatchingService>();
        }

        [Test, Order(1)]
        public void TestMatchingByScriptableObject()
        {
            LogAssert.Expect(LogType.Warning, new Regex(".*config object must be a QualityMatchingConfigObject.*"));
            LogAssert.Expect(LogType.Warning, new Regex(".*config loading failed.*"));
            var detail = _qualityMatchingService.DoMatching(null, "medium");
            Assert.IsNull(detail);

            var config = CreateTestConfig();
            LogAssert.Expect(LogType.Warning, new Regex(".*cannot find matching quality detail for device.*"));
            detail = _qualityMatchingService.DoMatching(config, "unknown");
            Assert.IsNull(detail);
            Assert.AreEqual(string.Empty, _qualityMatchingService.GetQualityDetailKey());

            detail = _qualityMatchingService.DoMatching(config, "medium");
            Assert.IsNotNull(detail);
            Assert.AreEqual(300, detail.Value.detailMap["shader_lod"]);
            Assert.AreEqual(900, detail.Value.detailMap["screen_resolution"]);
            Assert.AreEqual("medium", _qualityMatchingService.GetQualityDetailKey());

            detail = _qualityMatchingService.DoMatching(config, "high");
            Assert.IsNotNull(detail);
            Assert.AreEqual(400, detail.Value.detailMap["shader_lod"]);
            Assert.AreEqual(1080, detail.Value.detailMap["screen_resolution"]);
            Assert.AreEqual("high", _qualityMatchingService.GetQualityDetailKey());
            Object.DestroyImmediate(config);
        }

        [Test, Order(2)]
        public void TestMismatchedConfigEntriesAreRejected()
        {
            var config = CreateTestConfig();
            config.configList.RemoveAt(config.configList.Count - 1);

            LogAssert.Expect(LogType.Warning, new Regex(".*deviceKey and configList must be non-empty and have the same number of entries.*"));
            LogAssert.Expect(LogType.Warning, new Regex(".*config loading failed.*"));
            Assert.IsNull(_qualityMatchingService.DoMatching(config, "medium"));
            Assert.AreEqual(string.Empty, _qualityMatchingService.GetQualityDetailKey());
            Object.DestroyImmediate(config);
        }

        private static QualityMatchingConfigObject CreateTestConfig()
        {
            var config = ScriptableObject.CreateInstance<QualityMatchingConfigObject>();
            config.deviceKey = new List<string> { "low", "medium", "high" };
            config.configList = new List<QualityMatchingConfigObject.ConfigList>
            {
                CreateDetail(200, 720),
                CreateDetail(300, 900),
                CreateDetail(400, 1080),
            };
            return config;
        }

        private static QualityMatchingConfigObject.ConfigList CreateDetail(int shaderLod, int resolution)
        {
            return new QualityMatchingConfigObject.ConfigList
            {
                list = new List<QualityMatchingConfigObject.ConfigElement>
                {
                    new() { name = "shader_lod", value = shaderLod },
                    new() { name = "screen_resolution", value = resolution },
                },
            };
        }
    }
}

```

## Assets/JJCore/core/Tests/Runtime/Script/APMServices/UTQualityModifyService.cs

SHA256: 86399a961bbb3af9ca87b30910c406d2bdea25173d005bcba7e5c8db8781c14a

```csharp
using System.Collections.Generic;
using System.Text.RegularExpressions;
using jj.Core.Runtime;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TestTools;

namespace jj.Core.Tests.Runtime
{
    [TestFixture]
    [Category("APM_QualityModifyService")]
    public class UTQualityModifyService
    {
        private IQualityModifyService _qualityModifyService;

        [OneTimeSetUp]
        public void SetUp()
        {
            var injector = new ServiceInjector();
            injector.RegisterSelf();
            injector.Register<IQualityModifyService, QualityModifyService>();
            injector.Register<ILogService, LogService>();
            _qualityModifyService = injector.CreateOrGetInstance<IQualityModifyService>();
        }

        [Test, Order(1)]
        public void TestRegisterQualityHandler()
        {
        }

        [Test, Order(2)]
        public void TestQualityModify()
        {
            LogAssert.Expect(LogType.Warning, new Regex(".*quality detail map cannot be null.*"));
            _qualityModifyService.DoQualityModify(new QualityDetail());

            // 记录引擎原本参数
            var maxlod = Shader.globalMaximumLOD;
            var urpasset = (UniversalRenderPipelineAsset) GraphicsSettings.defaultRenderPipeline;
            var msaa = urpasset ? (MsaaQuality) urpasset.msaaSampleCount : MsaaQuality.Disabled;
            var quality = QualitySettings.GetQualityLevel();

            _qualityModifyService.DoQualityModify(_sTestQualityDetail);
            Assert.AreEqual(Shader.globalMaximumLOD, 200);
            var msaa2 = urpasset ? (MsaaQuality) urpasset.msaaSampleCount : MsaaQuality.Disabled;
            Assert.AreEqual(msaa2, (MsaaQuality) 1);
            Assert.AreEqual(QualitySettings.GetQualityLevel(), 4);

            // 恢复引擎原本参数
            Shader.globalMaximumLOD = maxlod;
            urpasset.msaaSampleCount = (int) msaa;
            QualitySettings.SetQualityLevel(quality);
        }

        private static readonly QualityDetail _sTestQualityDetail = new()
        {
            name = "test",
            detailMap = new Dictionary<string, int>()
            {
                ["shader_lod"] = 200,
                ["msaa"] = 1,
                ["unity_quality"] = 4,
                ["screen_resolution"] = 900,
            }
        };

        private class TestQualityModifyQualityHandler : IQualityHandler
        {
            public string ErrorCode => string.Empty;

            public bool Handle(QualityDetail qualityDetail)
            {
                return false;
            }

            public void Release()
            {
            }
        }
    }
}

```
